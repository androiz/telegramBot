import pickle
import logging
import time

from random import randint
from datetime import datetime

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from settings import (
    AWS_DYNAMO_ACCESS_KEY, AWS_DYNAMO_SECRET_KEY, PROXY, PROXY_AUTH_USER, PROXY_AUTH_PASS,
    PROXY_AUTH_URL, PROXY_AUTH_PROTOCOL, AWS_DYNAMO_REGION
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DynamoDB:
    table_name = None

    def __init__(self, config=None):
        self.client = boto3.client(
            'dynamodb',
            region_name=AWS_DYNAMO_REGION,
            aws_access_key_id=AWS_DYNAMO_ACCESS_KEY,
            aws_secret_access_key=AWS_DYNAMO_SECRET_KEY,
            config=config
        )

    def get(self, key, default=None):
        pass

    def set(self, key, value):
        pass

    def delete(self, key):
        pass


class DynamoDBConversations(DynamoDB):
    table_name = 'TelegramConversations'

    def delete(self, key):
        self.client.delete_item(
            TableName=self.table_name,
            Key={
                'ChatId': {
                    'N': str(key)
                }
            }
        )

    def get(self, key, default=None):
        try:
            _ = self.client.get_item(
                TableName=self.table_name,
                Key={
                    'ChatId': {
                        'N': str(key)
                    }
                }
            )
            return pickle.loads(_.get('Item', {}).get('State', {}).get('B'))
        except TypeError:
            logger.info(f'DynamoDB.get({key}): Key {key} does not exists')

        return default

    def set(self, key, value, ttl=60):
        self.client.put_item(
            TableName=self.table_name,
            Item={
                'ChatId': {
                    'N': str(key)
                },
                'ExpirationTime': {
                    'N': str(int(time.time()) + ttl)
                },
                'State': {
                    'B': pickle.dumps(value)
                },
            }
        )


class DynamoDBCalendar(DynamoDB):
    table_name = 'TelegramCalendar'

    def set_calendar(self, key_datetime, json_data):
        calendar_id = f'{datetime.now().timestamp()}{randint(100, 999)}'

        self.client.put_item(
            TableName=self.table_name,
            Item={
                'CalendarId': {
                    'N': calendar_id
                },
                'CalendarDT': {
                    'S': key_datetime.strftime('%Y%m%dT%H%M%S')
                },
                'Data': {
                    'B': pickle.dumps(json_data)
                },
            }
        )

        return calendar_id

    def get_calendar(self):
        _ = self.client.scan(
            TableName=self.table_name,
            ScanFilter={
                'CalendarDT': {
                    'AttributeValueList': [
                        {
                            'S': datetime.now().strftime('%Y%m%dT%H%M%S'),
                        }
                    ],
                    'ComparisonOperator': 'GE'
                }
            }
        )

        # Todo: Optimizar
        items = []
        for item in _.get('Items', []):
            data = pickle.loads(item.get('Data', {}).get('B'))

            data['calendar_id'] = item.get('CalendarId', {}).get('N')
            data['calendar_dt'] = item.get('CalendarDT', {}).get('S')

            items.append(data)

        items.sort(key=lambda _: _.get('calendar_dt'))
        return items[:3]

    def clean_calendar(self):
        _ = self.client.scan(
            TableName=self.table_name,
            # Limit=10,
            ScanFilter={
                'CalendarDT': {
                    'AttributeValueList': [
                        {
                            'S': datetime.now().strftime('%Y%m%dT%H%M%S'),
                        }
                    ],
                    'ComparisonOperator': 'LT'
                }
            }
        )

        items = _.get('Items', [])
        logger.info(f'Deleting {len(items)} items...')

        for item in items:
            self.client.delete_item(
                TableName='TelegramCalendar',
                Key={
                    'CalendarId': {
                        'N': str(item.get('CalendarId', {}).get('N'))
                    },
                    'CalendarDT': {
                        'S': item.get('CalendarDT', {}).get('S')
                    }
                }
            )

    def get_calendar_by_id(self, calendar_id):
        try:
            _ = self.client.scan(
                TableName=self.table_name,
                ScanFilter={
                    'CalendarId': {
                        'AttributeValueList': [
                            {
                                'N': calendar_id
                            }
                        ],
                        'ComparisonOperator': 'EQ'
                    }
                }
            )
        except ClientError:
            return

        if items := _.get('Items', []):
            return pickle.loads(items[0].get('Data', {}).get('B'))

    def set_calendar_by_id(self, calendar_id, json_data):
        try:
            _ = self.client.scan(
                TableName=self.table_name,
                ScanFilter={
                    'CalendarId': {
                        'AttributeValueList': [
                            {
                                'N': calendar_id
                            }
                        ],
                        'ComparisonOperator': 'EQ'
                    }
                }
            )
        except ClientError:
            return

        if items := _.get('Items', []):
            self.client.put_item(
                TableName='TelegramCalendar',
                Item={
                    'CalendarId': {
                        'N': items[0].get('CalendarId', {}).get('N')
                    },
                    'CalendarDT': {
                        'S': items[0].get('CalendarDT', {}).get('S')
                    },
                    'Data': {
                        'B': pickle.dumps(json_data)
                    },
                }
            )


dynamo_db_conversations = DynamoDBConversations(
    config=Config(proxies={'https': f'{PROXY_AUTH_PROTOCOL}://{PROXY_AUTH_USER}:{PROXY_AUTH_PASS}@{PROXY_AUTH_URL}'}) if PROXY else None
)

dynamo_db_calendar = DynamoDBCalendar(
    config=Config(proxies={'https': f'{PROXY_AUTH_PROTOCOL}://{PROXY_AUTH_USER}:{PROXY_AUTH_PASS}@{PROXY_AUTH_URL}'}) if PROXY else None
)


__all__ = ['dynamo_db_conversations', 'dynamo_db_calendar']
