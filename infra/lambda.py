import logging
import os

import boto3

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


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
