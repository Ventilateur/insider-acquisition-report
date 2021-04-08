import logging
from datetime import date, timedelta
from typing import List

from scrape.daywalker import list_sec4_data, list_sec4_files_of_date
import scrape.db as db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def make_chunks(big_list: List, nb_elem=100) -> List[List]:
    return [big_list[i:i + nb_elem] for i in range(0, len(big_list), nb_elem)]


# The very first step, will fetch all SEC 4 file locations within a chosen date
# Returns {'data': [urls], 'date': '2021-04-04'}
def fetch_metadata(event, _):
    # If the date is not asked, always fetch data from yesterday
    current_date = date.today() - timedelta(1)
    if event and 'date' in event:
        current_date = date.fromisoformat(event['date'])

    if db.is_data_already_fetched(current_date):
        log.info(f"Data was already fetched for {current_date}")
        return {}

    urls = list_sec4_files_of_date(current_date)
    log.info(f"Found {len(urls)} files")

    # Return a list of chunks for easier processing
    return {
        'urls': make_chunks(urls),
        'date': str(current_date)
    }


# Second step, will block the state in DynamoDB
# Returns {'urls': [[urls]], 'date': '2021-04-04'}
def save_state(event, _):
    db.save_state(event['date'])
    return event


# Third step, will be performed with Map in AWS Step Function
# Input will be {'urls': [urls], 'date': '2021-04-04'}, from Map parameters
# Returns {'urls': [urls], 'data': [ ( field values ) ]}
def fetch_data(event, _):
    urls = event['urls']
    data_list = list_sec4_data(urls)
    return {
        'urls': urls,
        'data': [row for data in data_list for row in data.flatten(event['date'])]
    }


# Final step, will be performed with Map in AWS Step Function
# Input will be {'urls': [urls], 'data': [ ( field values ) ]}
# Returns {}
def save_data(event, _):
    db.save_to_db(event['data'])
    return {}


# Error handling step, only triggered if the 3rd or 4th fails
# Input will be [urls], from input path
def save_unprocessed_files(event, _):
    db.save_unprocessed_files(event)
