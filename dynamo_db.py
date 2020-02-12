import pickle
import logging
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
    def __init__(self, table_name=None, config=None):
        self.table_name = table_name
        self.client = boto3.client(
            'dynamodb',
            region_name=AWS_DYNAMO_REGION,
            aws_access_key_id=AWS_DYNAMO_ACCESS_KEY,
            aws_secret_access_key=AWS_DYNAMO_SECRET_KEY,
            config=config
        )

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except TypeError:
            logger.info(f'DynamoDB.get({key}): Key {key} does not exists')

        return default

    def set(self, key, value):
        self.__setitem__(key, value)

    def delete(self, key):
        self.__delitem__(key)

    def __delitem__(self, key):
        """
        self.client.delete_item(
            TableName=self.table_name,
            Key={
                'ChatId': {
                    'N': 2
                }
            }
        )
        """
        self.client.delete_item(
            TableName=self.table_name,
            Key={
                'ChatId': {
                    'N': str(key)
                }
            }
        )

    def __getitem__(self, key):
        """
        response = client.get_item(
            TableName='TelegramConversations',
            Key={
                'ChatId': {
                    'S': '2'
                }
            }
        )
        """
        _ = self.client.get_item(
            TableName=self.table_name,
            Key={
                'ChatId': {
                    'N': str(key)
                }
            }
        )
        return pickle.loads(_.get('Item', {}).get('State', {}).get('B'))

    def __setitem__(self, key, value):
        """
        client.put_item(
            TableName='TelegramConversations',
            Item={
                'ChatId': {
                    'S': '2'
                },
                'state': {
                    'S': 'prueba'
                },
            }
        )
        """
        self.client.put_item(
            TableName=self.table_name,
            Item={
                'ChatId': {
                    'N': str(key)
                },
                'State': {
                    'B': pickle.dumps(value)
                },
            }
        )

    def set_calendar(self, key_datetime, json_data):
        calendar_id = f'{datetime.now().timestamp()}{randint(100, 999)}'

        self.client.put_item(
            TableName='TelegramCalendar',
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
            TableName='TelegramCalendar',
            # Limit=10,
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
            TableName='TelegramCalendar',
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
        for item in _.get('Items', []):
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
                TableName='TelegramCalendar',
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
                TableName='TelegramCalendar',
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


dynamo_db = DynamoDB(
    table_name='TelegramConversations',
    config=Config(proxies={'https': f'{PROXY_AUTH_PROTOCOL}://{PROXY_AUTH_USER}:{PROXY_AUTH_PASS}@{PROXY_AUTH_URL}'}) if PROXY else None
)


__all__ = ['dynamo_db']
