import logging
from datetime import date, timedelta
from typing import List

from scrape.daywalker import is_data_already_fetched, list_sec4_data, list_sec4_files_of_date
from scrape.db import save_state, save_to_db, save_unprocessed_files

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def make_chunks(big_list: List, nb_elem=100) -> List[List]:
    return [big_list[i:i + nb_elem] for i in range(0, len(big_list), nb_elem)]


def fetch_metadata(event, _):
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
