import json
import logging
import os
import re
import time
import uuid
from datetime import date, timedelta
from enum import IntEnum
from typing import List, Optional
from xml.etree.ElementTree import XMLPullParser

import boto3
import pymysql
import requests
from requests import HTTPError, Response

from scrape import const
from scrape.exceptions import CannotFetchDataException, MissingDataException, UnneededDataException
from scrape.models import SEC4Data

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class IdxColumn(IntEnum):
    CIK = 0,
    NAME = 1,
    TYPE = 2,
    DATE = 3,
    FILE = 4


_SEC4_TYPE = "4"
_TIME_BETWEEN_REQUEST = 0.5


def _request(url) -> Response:
    log.info(f"Request URL: {url}")
    resp = requests.get(url, headers={'user-agent': str(uuid.uuid4())})
    try:
        resp.raise_for_status()
    except HTTPError:
        log.error(json.dumps({
            "code": resp.status_code,
            "message": resp.content
        }))
        raise CannotFetchDataException(url)
    return resp


def list_sec4_files_of_date(request_date: date) -> List[str]:
    log.info(f"Finding sec4 files of {request_date}")
    files_loc = {}

    if request_date.weekday() >= 5:
        log.info(f"{request_date} is weekend, skipped")
        return []

    base = "https://www.sec.gov/Archives"
    quarter = (request_date.month + 2) // 3
    url = f"{base}/edgar/daily-index/{request_date.year}/QTR{quarter}/master.{request_date.strftime('%Y%m%d')}.idx"

    r = _request(url)

    for line in r.iter_lines():
        fields = line.decode("UTF-8").split("|")
        if len(fields) == len(IdxColumn) and fields[IdxColumn.TYPE] == _SEC4_TYPE:
            file_path = fields[IdxColumn.FILE]
            accession_code = os.path.splitext(file_path.split("/")[-1])[0]
            files_loc[accession_code] = f"{base}/{file_path}"

    return list(files_loc.values())


_START_TOKEN = "<ownershipDocument>"
_STOP_TOKEN = "</ownershipDocument>"

_start_p = re.compile(_START_TOKEN)
_stop_p = re.compile(_STOP_TOKEN)


def get_sec4_data(url) -> Optional[SEC4Data]:
    r = _request(url)

    feed = False
    parser = XMLPullParser()
    for line in r.iter_lines():
        if not feed and _start_p.match(line.decode("utf-8")):
            feed = True

        if feed:
            parser.feed(line)

        if _stop_p.match(line.decode("utf-8")):
            break

    data = None
    for _, elem in parser.read_events():
        if elem.tag == SEC4Data.xml_root:
            try:
                data = SEC4Data(elem, url)
            except (MissingDataException, UnneededDataException):
                pass
            break

    return data


def list_sec4_data(urls) -> List[SEC4Data]:
    data = []
    total = len(urls)
    current = 1
    for url in urls:
        log.info(f"Getting ({current}/{total}): {url}")
        sec4_data = get_sec4_data(url)
        if sec4_data is not None:
            data.append(sec4_data)
        current += 1
        time.sleep(_TIME_BETWEEN_REQUEST)
    return data


def is_data_already_fetched(request_date: date) -> bool:
    db = boto3.resource('dynamodb')
    table = db.Table('SEC4States')
    requested_state = table.get_item(
        Key={
            'State': str(request_date)
        },
        ConsistentRead=True
    )
    return 'Item' in requested_state


def _get_db_conn() -> pymysql.Connection:
    return pymysql.connect(
        host=os.environ['RDS_HOST'],
        user=os.environ['RDS_USERNAME'],
        password=os.environ['RDS_PASSWORD'],
        database=os.environ['RDS_DB_NAME'],
        cursorclass=pymysql.cursors.DictCursor
    )


def save_to_db(data_list: List[SEC4Data]):
    rows = [row for data in data_list for row in data.flatten()]
    log.info(f"Putting {len(rows)} records into database")
    with _get_db_conn() as connection:
        with connection.cursor() as cursor:
            insert_sql = f"INSERT INTO {const.SEC4_TRANSACTIONS_TABLE} VALUES ({', '.join(['%s'] * 9)})"
            for row in rows:
                cursor.execute(insert_sql, row)
        connection.commit()


def save_unprocessed_files(files: List[str]):
    with _get_db_conn() as connection:
        with connection.cursor() as cursor:
            insert_sql = f"INSERT INTO {const.SEC4_UNPROCESSED_FILES_TABLE} VALUES (%s)"
            for file in files:
                cursor.execute(insert_sql, file)
        connection.commit()


def save_state(request_date: date):
    db = boto3.resource('dynamodb')
    table = db.Table('SEC4States')

    # Save the first date for the first time
    first_date = table.get_item(
        Key={
            'State': 'first_date'
        },
        ConsistentRead=True
    )
    if 'Item' not in first_date:
        log.info(f"Saving {request_date} as first date")
        table.put_item(
            Item={
                'State': 'first_date',
                'Date': str(request_date)
            }
        )

    # Update the last date to current date
    log.info(f"Saving {request_date} as last date")
    table.put_item(
        Item={
            'State': 'last_date',
            'Date': str(request_date)
        }
    )

    # Put the current date in states
    log.info(f"Saving {request_date} as state")
    table.put_item(
        Item={
            'State': str(request_date)
        }
    )


def make_chunks(big_list: List, nb_elem=100) -> List[List]:
    return [big_list[i:i + nb_elem] for i in range(0, len(big_list), nb_elem)]


def lambda_fetch_metadata(event, _):
    # If the date is not asked, always fetch data from yesterday
    current_date = date.today() - timedelta(1)
    if event and 'date' in event:
        current_date = date.fromisoformat(event['date'])

    if is_data_already_fetched(current_date):
        log.info(f"Data was already fetched for {current_date}")
        return {}

    urls = list_sec4_files_of_date(current_date)
    log.info(f"Found {len(urls)} files")

    # Block the current date state
    save_state(current_date)

    # Return a list of chunks for easier processing
    return {
        'data': make_chunks(urls)
    }


def lambda_fetch_and_save(event, _):
    try:
        data = list_sec4_data(event)
        save_to_db(data)
    except Exception as e:
        log.error(e)
        log.info(f"Saving {len(event)} unprocessed files due to unexpected error")
        save_unprocessed_files(event)


def lambda_handler(event, _):
    # If the date is not asked, always fetch data from yesterday
    current_date = date.today() - timedelta(1)
    if event and 'date' in event:
        current_date = date.fromisoformat(event['date'])

    if is_data_already_fetched(current_date):
        log.info(f"Data was already fetched for {current_date}")
        return

    urls = list_sec4_files_of_date(current_date)
    log.info(f"Found {len(urls)} files")
    data = list_sec4_data(urls)
    save_to_db(data)
    save_state(current_date)


if __name__ == '__main__':
    os.environ['AWS_DEFAULT_REGION'] = 'eu-west-3'
    lambda_handler({}, {})