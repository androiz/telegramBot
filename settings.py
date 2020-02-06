import os
from dotenv import load_dotenv


load_dotenv(dotenv_path='.env')


TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_WEBHOOK_URL = os.getenv('TELEGRAM_WEBHOOK_URL')

PROXY = os.getenv('PROXY_AUTH_URL')
PROXY_AUTH_USER = os.getenv('PROXY_AUTH_USER')
PROXY_AUTH_PASS = os.getenv('PROXY_AUTH_PASS')
PROXY_AUTH_URL = os.getenv('PROXY_AUTH_URL')

AWS_DYNAMO_ACCESS_KEY = os.getenv('AWS_DYNAMO_ACCESS_KEY')
AWS_DYNAMO_SECRET_KEY = os.getenv('AWS_DYNAMO_SECRET_KEY')
AWS_DYNAMO_REGION = os.getenv('AWS_DYNAMO_REGION')
AWS_DYNAMO_TABLE = os.getenv('AWS_DYNAMO_TABLE')

SQLITE_DB = os.getenv('SQLITE_DB')
