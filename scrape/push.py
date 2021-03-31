from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List

import boto3

import scrape.labels as labels
from scrape.edgar import list_sec4_files_of_date
from scrape.models import SEC4Data
from scrape.sec4 import list_sec4_data

_TMP_NAME = 'name'
_TMP_TRANSACTIONS = 'transactions'
DYNAMODB_TABLE = 'sec4'
NB_RETAIN_DAYS = 730


def aggregate_data(data_list: List[SEC4Data]):
    result = {}
    for d in data_list:
        for t in d.transactions:
            daily_data = result.get(t.date, None)
            if daily_data is None:
                daily_data = {d.company_code: None}
                result[t.date] = daily_data

            company_daily_data = daily_data.get(d.company_code, None)
            if company_daily_data is None:
                company_daily_data = {
                    _TMP_NAME: d.company_name,
                    _TMP_TRANSACTIONS: []
                }
                daily_data[d.company_code] = company_daily_data

            company_daily_data[_TMP_TRANSACTIONS].append({
                labels.INSIDERS: [str(insider) for insider in d.insiders],
                labels.PRICE: Decimal(str(t.price_per_share)),
                labels.NB_SHARES: t.nb_shares,
                labels.SECURITY_TYPE: t.security_title,
                labels.BUY_OR_SELL: 'B' if t.is_acquire else 'S',
                labels.SEC4_FILE_LOC: d.sec4_file_loc
            })
    return result


def save_to_dynamodb(aggregated_data):
    ttl = int((datetime.today() + timedelta(NB_RETAIN_DAYS)).timestamp())
    db = boto3.resource('dynamodb')
    with db.Table(DYNAMODB_TABLE).batch_writer() as batch:
        for transaction_date, daily_data in aggregated_data.items():
            for company_code, company_daily_data in daily_data.items():
                batch.put_item(Item={
                    labels.TRANSACTION_DATE: transaction_date,
                    labels.COMPANY_CODE: company_code,
                    labels.COMPANY_NAME: company_daily_data[_TMP_NAME],
                    labels.TRANSACTIONS: company_daily_data[_TMP_TRANSACTIONS],
                    labels.TTL: ttl
                })


def lambda_handler(event, context):
    files = list_sec4_files_of_date(date.today() - timedelta(1))
    print(f"Found {len(files)} files")
    latest_data = list_sec4_data(files)
    save_to_dynamodb(aggregate_data(latest_data))
