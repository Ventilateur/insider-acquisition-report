import re
from typing import Any, Mapping, Optional
from xml.etree.ElementTree import XMLPullParser

import requests

from exceptions import MissingDataException, UnneededDataException
from models import SEC4Data

_START_TOKEN = "<ownershipDocument>"
_STOP_TOKEN = "</ownershipDocument>"

_start_p = re.compile(_START_TOKEN)
_stop_p = re.compile(_STOP_TOKEN)


def get_sec4_data(url) -> Optional[SEC4Data]:
    r = requests.get(url)
    r.raise_for_status()

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


def list_sec4_data(urls) -> Mapping[str, Any]:
    data = {}
    for url in urls:
        sec4_data = get_sec4_data(url)
        if sec4_data is not None:

            insiders = [str(insider) for insider in sec4_data.insiders]
            transactions = [
                {**transaction.to_dict(), "sec4_file": sec4_data.form_url}
                for transaction in sec4_data.transactions
            ]

            prev_data = data.get(sec4_data.company, None)
            if prev_data is None:
                data[sec4_data.company] = {
                    "insiders": insiders,
                    "transactions": transactions
                }
            else:
                prev_data["insiders"] += insiders
                prev_data["transactions"] += transactions

    return data


def lambda_handler(event, _) -> Mapping[str, Any]:
    return list_sec4_data(event["urls"])
