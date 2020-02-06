import pickle
import logging

import boto3
from botocore.config import Config

from settings import (
    AWS_DYNAMO_ACCESS_KEY, AWS_DYNAMO_SECRET_KEY, PROXY, PROXY_AUTH_USER, PROXY_AUTH_PASS, AWS_DYNAMO_REGION
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

    # def pop(self, key):
    #     return self.__delitem__(key)

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


dynamo_db = DynamoDB(
    table_name='TelegramConversations',
    config=Config(proxies={'https': f'http://{PROXY_AUTH_USER}:{PROXY_AUTH_PASS}@proxy.indra.es:8080'}) if PROXY else None
)


__all__ = ['dynamo_db']
