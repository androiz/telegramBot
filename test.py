from dynamo_db import dynamo_db
from spell_info.pool import sqlite_db


# row = sqlite_db.get_hechizo('manos ardientes')

dynamo_db.clean_calendar()

for item in dynamo_db.get_calendar():
    print(item.get('event_title'), item.get('event_date'))
