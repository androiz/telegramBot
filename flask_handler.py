import telepot
from flask import Flask, request

from views import flow


app = Flask(__name__)

UPDATE_ID_ITER = None

TELEGRAM_MSG_TYPES = [
    'callback_query', 'message',
]


@app.route("/", methods=['GET', 'POST'])
def webhook():
    global UPDATE_ID_ITER

    json_data = request.json
    if json_data:
        update_id = json_data.get('update_id')

        if update_id:
            if not UPDATE_ID_ITER or update_id > UPDATE_ID_ITER:
                key = telepot._find_first_key(json_data, TELEGRAM_MSG_TYPES)
                flow(json_data[key])

            UPDATE_ID_ITER = update_id

    return app.response_class(response={}, status=200, mimetype='application/json')
