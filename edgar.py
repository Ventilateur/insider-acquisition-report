from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from http import HTTPStatus
from typing import List

import requests
from requests import HTTPError

_VALID_NB_FIELDS = 5
_SEC4_TYPE = "4"
_TYPE_IDX = 2
_FILE_URL_IDX = 4


def list_sec4_files(request_date: date):
    print(f"Finding sec4 files of {request_date}")
    files_loc = set()

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
        if len(fields) == _VALID_NB_FIELDS and fields[_TYPE_IDX] == _SEC4_TYPE:
            files_loc.add(f"{base}/{fields[_FILE_URL_IDX]}")

    return files_loc


def gather_weekly_sec4_files():
    day = date.today()
    sec4_files = set()
    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {executor.submit(list_sec4_files, day - timedelta(i)) for i in range(1, 2)}
        for future in as_completed(futures):
            sec4_files |= future.result(timeout=30)
    return sec4_files


def make_chunks(big_list, nb_elem):
    return [big_list[i:i + nb_elem] for i in range(0, len(big_list), nb_elem)]


def lambda_handler(event, context) -> List[List[str]]:
    files_list = gather_weekly_sec4_files()
    return make_chunks(files_list, 10)
