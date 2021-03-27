import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from enum import IntEnum
from http import HTTPStatus
from typing import List

import requests
from requests import HTTPError


class IdxColumn(IntEnum):
    CIK = 0,
    NAME = 1,
    TYPE = 2,
    DATE = 3,
    FILE = 4


_SEC4_TYPE = "4"


def list_sec4_files_of_date(request_date: date) -> List[str]:
    print(f"Finding sec4 files of {request_date}")
    files_loc = {}

    if request_date.weekday() >= 5:
        print(f"{request_date} is weekend, skipped")
        return files_loc

    base = "https://www.sec.gov/Archives"
    quarter = (request_date.month + 2) // 3
    url = f"{base}/edgar/daily-index/{request_date.year}/QTR{quarter}/master.{request_date.strftime('%Y%m%d')}.idx"

    r = requests.get(url)
    try:
        r.raise_for_status()
    except HTTPError as e:
        if e.response.status_code == HTTPStatus.FORBIDDEN:
            print(f"No data for {request_date}")
            return files_loc
        else:
            raise e

    for line in r.iter_lines():
        fields = line.decode("UTF-8").split("|")
        if len(fields) == len(IdxColumn) and fields[IdxColumn.TYPE] == _SEC4_TYPE:
            file_path = fields[IdxColumn.FILE]
            accession_code = os.path.splitext(file_path.split("/")[-1])[0]
            files_loc[accession_code] = f"{base}/{fields[IdxColumn.FILE]}"

    return list(files_loc.values())


def list_sec4_files(start_date=date.today(), date_range=7) -> List[str]:
    sec4_files = []
    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {executor.submit(list_sec4_files_of_date, start_date - timedelta(i)) for i in range(1, date_range)}
        for future in as_completed(futures):
            sec4_files += future.result(timeout=30)
    return sec4_files


def make_chunks(big_list, nb_elem=10):
    return [big_list[i:i + nb_elem] for i in range(0, len(big_list), nb_elem)]


def lambda_handler(event, _) -> List[List[str]]:
    files_list = list_sec4_files(event["config"]["nb_days"])
    return make_chunks(files_list, event["config"]["chunk_size"])
