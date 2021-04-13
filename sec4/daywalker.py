import json
import logging
import os
import re
import time
import uuid
from datetime import date
from enum import IntEnum
from typing import List, Optional
from xml.etree.ElementTree import XMLPullParser

import requests
from requests import HTTPError, Response

from sec4.exceptions import CannotFetchDataException, MissingDataException, UnneededDataException
from sec4.models import SEC4Data

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


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
