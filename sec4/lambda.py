import json
import logging
import os
from datetime import date, timedelta
from typing import List

import boto3

from sec4.daywalker import list_sec4_data, list_sec4_files_of_date
import sec4.db as db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def make_chunks(big_list: List, nb_elem=100) -> List[List]:
    return [big_list[i:i + nb_elem] for i in range(0, len(big_list), nb_elem)]


# The very first step, check if there should be data to fetch
# Input  {'date': '2021-01-01'} or None
# Output {'date': '2021-01-01', 'proceed': true}
def pre_fetch(event, _):
    # If the date is not asked, always fetch data from yesterday
    current_date = date.today() - timedelta(1)
    if event and 'date' in event:
        current_date = date.fromisoformat(event['date'])

    if current_date.weekday() >= 5:
        # Only proceed if it's weekday
        log.info(f"{current_date} is weekend, skipped")
        proceed = False
    else:
        # Proceed if there is no data for current date or the data is incomplete
        proceed = db.should_fetch_data(current_date)

    return {
        'date': str(current_date),
        'proceed': proceed
    }


# Second step, fetch all SEC 4 file locations within the chosen date
# Input  {'date': '2021-01-01', 'proceed': true}
# Output {'date': '2021-01-01', 'urls': [[urls], [urls], ...]}
def fetch_metadata(event, _):
    current_date = event['date']
    urls = list_sec4_files_of_date(date.fromisoformat(current_date))
    log.info(f"Found {len(urls)} files")

    # Return a list of chunks for easier processing
    return {
        'date': current_date,
        'urls': make_chunks(urls)
    }


# Third step, will be performed with Map in AWS Step Function
# Input  {'date': '2021-01-01', 'urls': [urls]}
# Output {'date': '2021-01-01', 'urls': [urls], 'data': [[values], [values], ...]}
def fetch_data(event, _):
    urls = event['urls']
    query_date = event['date']
    data_list = list_sec4_data(urls)
    return {
        'date': query_date,
        'urls': urls,
        'data': [row for data in data_list for row in data.flatten(query_date)]
    }


# Forth step, will be performed with Map in AWS Step Function
# Input  {'date': '2021-01-01', 'urls': [urls], 'data': [[values], [values], ...]}
# Output {'date': '2021-01-01'}
def save_data(event, _):
    data = event['data']
    log.info(f"Putting {len(data)} records into database")
    db.save_to_db(data)
    return {
        'date': event['date']
    }


# Fifth step, save state to either complete or incomplete
# Input  {'date': '2021-01-01', 'error': {error}} or {'date': '2021-01-01', 'urls': [[urls], [urls], ...]}
# Output {}
def save_state(event, _):
    error = event.get('error', None)
    if error:
        log.error(json.dumps(error))

    success = error is None
    db.save_state(event['date'], success)
    return {}


def start_db(event, _):
    client = boto3.client('rds')
    try:
        client.start_db_instance(DBInstanceIdentifier=os.environ['DB_IDENTIFIER'])
    except client.exceptions.InvalidDBInstanceStateFault:
        log.info('DB has already started')


def stop_db(event, _):
    client = boto3.client('rds')
    try:
        client.stop_db_instance(DBInstanceIdentifier=os.environ['DB_IDENTIFIER'])
    except client.exceptions.InvalidDBInstanceStateFault:
        log.info('DB has already stopped')
