from enum import Enum


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
