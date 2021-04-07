import os
import pymysql.cursors

# Connect to the database
import scrape.const as const

table = f"""
    CREATE TABLE IF NOT EXISTS {const.SEC4_TRANSACTIONS_TABLE} (
        {const.TRANSACTION_DATE} DATE NOT NULL,
        {const.COMPANY_CODE} VARCHAR(10) NOT NULL,
        {const.COMPANY_NAME} VARCHAR(1024) NOT NULL,
        {const.INSIDERS} JSON NOT NULL,
        {const.BUY_OR_SELL} ENUM('B', 'S') NOT NULL,
        {const.PRICE} DECIMAL(10, 5) NOT NULL,
        {const.NB_SHARES} INTEGER NOT NULL,
        {const.SECURITY_TITLE} VARCHAR(255) NOT NULL,
        {const.SEC4_FILE_LOC} VARCHAR(1024) NOT NULL
    );
"""

indexes = [
    f"CREATE INDEX idx_{const.TRANSACTION_DATE} ON {const.SEC4_TRANSACTIONS_TABLE} ({const.TRANSACTION_DATE})",
    f"CREATE INDEX idx_{const.COMPANY_CODE} ON {const.SEC4_TRANSACTIONS_TABLE} ({const.COMPANY_CODE})",
    f"CREATE INDEX idx_{const.BUY_OR_SELL} ON {const.SEC4_TRANSACTIONS_TABLE} ({const.BUY_OR_SELL})",
]


def lambda_handler(event, context):
    connection = pymysql.connect(host=os.environ['RDS_HOST'],
                                 user=os.environ['RDS_USERNAME'],
                                 password=os.environ['RDS_PASSWORD'],
                                 database=os.environ['RDS_DB_NAME'],
                                 cursorclass=pymysql.cursors.DictCursor)

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(table)
            for index in indexes:
                cursor.execute(index)
        connection.commit()


if __name__ == '__main__':
    lambda_handler(None, None)
