import re
from typing import List
from xml.etree.ElementTree import XMLPullParser

import requests

from exceptions import MissingDataException, UnneededDataException
from models import SEC4Data

_START_TOKEN = "<ownershipDocument>"
_STOP_TOKEN = "</ownershipDocument>"

_start_p = re.compile(_START_TOKEN)
_stop_p = re.compile(_STOP_TOKEN)


def get_sec4_data(url):
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
                data = SEC4Data(elem)
            except (MissingDataException, UnneededDataException):
                pass
            break

    return data


def list_sec4_data(urls) -> List[List]:
    data = []
    for url in urls:
        sec4_data = get_sec4_data(url)
        if sec4_data is not None:
            data += sec4_data.to_list()
    return data


def lambda_handler(event, context) -> List[List]:
    return list_sec4_data(event["urls"])