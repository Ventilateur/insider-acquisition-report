import logging
import os
from datetime import date
from typing import List, Tuple

import boto3
import pymysql

from scrape import const

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def _get_db_conn() -> pymysql.Connection:
    return pymysql.connect(
        host=os.environ['RDS_HOST'],
        user=os.environ['RDS_USERNAME'],
        password=os.environ['RDS_PASSWORD'],
        database=os.environ['RDS_DB_NAME'],
        cursorclass=pymysql.cursors.DictCursor
    )


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


def save_to_db(rows: List[Tuple]):
    log.info(f"Putting {len(rows)} records into database")
    with _get_db_conn() as connection:
        with connection.cursor() as cursor:
            insert_sql = f"INSERT INTO {const.SEC4_TRANSACTIONS_TABLE} VALUES ({', '.join(['%s'] * 10)})"
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


def save_state(request_date: str):
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
                'Date': request_date
            }
        )

    # Update the last date to current date
    log.info(f"Saving {request_date} as last date")
    table.put_item(
        Item={
            'State': 'last_date',
            'Date': request_date
        }
    )

    # Put the current date in states
    log.info(f"Saving {request_date} as state")
    table.put_item(
        Item={
            'State': request_date
        }
    )
