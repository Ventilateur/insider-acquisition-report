from enum import Enum

SEC4_TRANSACTIONS_TABLE = 'sec4_transactions'
COMPANY_CODE = 'company_code'
COMPANY_NAME = 'company_name'
INSIDERS = 'insiders'
BUY_OR_SELL = 'buy_or_sell'
PRICE = 'price'
NB_SHARES = 'nb_shares'
TRANSACTION_DATE = 'transaction_date'
SECURITY_TITLE = 'security_title'
SEC4_FILE_LOC = "sec4_file_location"


class sec4_transactions(Enum):
    transaction_date = 1
    company_code = 2
    company_name = 3
    insiders = 4
    buy_or_sell = 5
    price = 6
    nb_shares = 7
    security_title = 8
    sec4_file_location = 9
    sec4_file_date = 10


class sec4_query_states(Enum):
    query_date = 1
    completed = 2
