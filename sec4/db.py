import json
import logging
import os
from datetime import date
from typing import List, Tuple

import pymysql

from sec4 import const
from sec4.const import sec4_query_states, sec4_transactions

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def _get_db_conn() -> pymysql.Connection:
    return pymysql.connect(
        host=os.environ['RDS_HOST'],
        user=os.environ['RDS_USERNAME'],
        password=os.environ['RDS_PASSWORD'],
        database=os.environ['RDS_DB_NAME'],
        cursorclass=pymysql.cursors.DictCursor
    )


def should_fetch_data(request_date: date) -> bool:
    with _get_db_conn() as connection:
        should_fetch = False
        with connection.cursor() as cursor:
            query_state_sql = (
                f"SELECT {sec4_query_states.query_date.name}, {sec4_query_states.completed.name} "
                f"FROM {sec4_query_states.__name__} "
                f"WHERE {sec4_query_states.query_date.name} = %s"
            )
            cursor.execute(query_state_sql, request_date)
            result = cursor.fetchone()
            log.info(f"Query state for {request_date}: {json.dumps(result)}")

            if result is None:
                should_fetch = True
            elif result['completed'] != 1:
                log.info('Delete incomplete data')
                delete_incomplete_data_sql = (
                    f"DELETE FROM {sec4_transactions.__name__} WHERE {sec4_transactions.sec4_file_date} = %s"
                )
                cursor.execute(delete_incomplete_data_sql, request_date)
                should_fetch = True

        connection.commit()
        return should_fetch


def save_to_db(rows: List[Tuple]):
    with _get_db_conn() as connection:
        with connection.cursor() as cursor:
            insert_sql = f"INSERT INTO {const.SEC4_TRANSACTIONS_TABLE} VALUES ({', '.join(['%s'] * 10)})"
            for row in rows:
                cursor.execute(insert_sql, row)
        connection.commit()


def save_state(request_date: str, success: bool):
    with _get_db_conn() as connection:
        with connection.cursor() as cursor:
            insert_sql = (
                f"INSERT INTO {sec4_query_states.__name__} "
                f"({sec4_query_states.query_date.name}, {sec4_query_states.completed.name}) "
                f"VALUES (%s, %s)"
            )
            cursor.execute(insert_sql, (request_date, 1 if success else 0))
        connection.commit()
