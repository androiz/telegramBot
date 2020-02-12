import logging
import re
from datetime import datetime

import telepot
from telegramcalendar import TelegramCalendar
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove


from settings import *
from dynamo_db import dynamo_db
from dice_roll import get_dice_roll
from spell_info.pool import sqlite_db
from spell_info.utils import get_spell_type_sentence
from messages import START_MSG, HELP_MSG, TEMPLATE_EVENT


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


if PROXY:
    auth_basic = None
    if PROXY_AUTH_USER and PROXY_AUTH_PASS:
        auth_basic = (PROXY_AUTH_USER, PROXY_AUTH_PASS)

    telepot.api.set_proxy(f'{PROXY_AUTH_PROTOCOL}://{PROXY_AUTH_URL}', basic_auth=auth_basic)


bot = telepot.Bot(TELEGRAM_TOKEN)
bot.setWebhook('')
bot.setWebhook(TELEGRAM_WEBHOOK_URL)
bot.getMe()


def flow(msg):
    flavor = telepot.flavor(msg)
    logger.info(f'Flavor: {flavor} - Message: {msg}')

    if flavor == 'chat':
        if is_start_cmd(msg):
            chat_id = msg['chat']['id']
            bot.sendMessage(chat_id, START_MSG, reply_markup=get_start_keyboard())
        elif is_help_cmd(msg):
            chat_id = msg['chat']['id']
            bot.sendMessage(chat_id, HELP_MSG)
        elif is_create_event_cmd(msg):
            chat_id = msg['chat']['id']
            first_name = msg.get('chat', {}).get('first_name', '')
            last_name = msg.get('chat', {}).get('last_name', '')

            event_data = {
                'event_title': '<Título>',
                'event_date': 'dd/mm/yyyy',
                'event_time': 'HH:MM',
                'event_address': '<Address>',
                'event_master': f'{first_name} {last_name}',
                'event_players_limit': 0,
                'event_players': {}
            }

            bot.sendMessage(
                chat_id,
                TEMPLATE_EVENT.format(
                    event_title=event_data.get('event_title', ''),
                    event_date=event_data.get('event_date', ''),
                    event_time=event_data.get('event_time', ''),
                    event_address=event_data.get('event_address', ''),
                    event_master=event_data.get('event_master', ''),
                    event_free=event_data.get('event_players_limit', 0) - len(event_data.get('event_players', {})),
                    event_players=''.join([f'\n---{name}' for _, name in event_data.get('event_players', {}).items()])
                ),
                parse_mode='Markdown',
                reply_markup=get_create_event_keyboard()
            )

            dynamo_db.set(chat_id, {
                'state': 'create_event',
                'extra': {
                    'editing_status': None,
                    'event_data': event_data
                }
            })
        elif is_join_event_cmd(msg):
            process_cmd(msg)
        else:
            process_text(msg)
    elif flavor == 'callback_query':
        process_callback(msg)


def process_cmd(msg):
    """
    Procesamos el cmd recibido
    """
    chat_id = msg.get('chat', {}).get('id')

    command = msg['text'].split(' ')
    if command[0] == '/join_event':
        event_data = dynamo_db.get_calendar_by_id(command[-1])
        print(event_data)
        if event_data:
            first_name = msg.get('chat', {}).get('first_name', '')
            last_name = msg.get('chat', {}).get('last_name', '')
            username = msg.get('from', {}).get('username', '')

            if username not in event_data['event_players'] and len(event_data['event_players']) < event_data['event_players_limit']:
                event_data['event_players'][username] = f'{first_name} {last_name}'

                dynamo_db.set_calendar_by_id(command[-1], event_data)

                bot.sendMessage(chat_id, 'Te has unido al evento correctamente', reply_markup=get_start_keyboard())
            else:
                bot.sendMessage(chat_id, 'Ya te has unido a este evento', reply_markup=get_start_keyboard())
        else:
            bot.sendMessage(chat_id, 'Se ha producido un error. Inténtalo más tarde.', reply_markup=get_start_keyboard())


def process_text(msg):
    """
    Procesamos el texto recibido, en base al estado del chat
    """
    chat_id = msg.get('chat', {}).get('id')

    # Get State
    chat_json = dynamo_db.get(chat_id)
    if chat_json:
        chat_state = chat_json.get('state')

        if chat_state == 'roll_dice':
            try:
                dice_amount = int(msg.get('text', ''))
            except (TypeError, ValueError):
                bot.sendMessage(chat_id, 'El valor introducido no es válido. Introduce un valor numérico')
                return

            if dice_amount:
                dice_face = chat_json.get('extra', {}).get('dice_face')

                bot.sendMessage(chat_id, get_dice_roll(dice_amount, dice_face), reply_markup=get_start_keyboard())
                dynamo_db.delete(chat_id)
        elif chat_state == 'get_spell_info':
            spell_name = msg.get('text', '')

            row = sqlite_db.get_hechizo(spell_name)
            if row:
                chat_json['extra'] = {
                    'spell_name': spell_name,
                    'row': row
                }
                bot.sendMessage(chat_id, 'Selecciona que quieres saber', reply_markup=get_spell_type_keyboard())
                dynamo_db.set(chat_id, chat_json)
            else:
                bot.sendMessage(chat_id, 'No hemos encontrado ese hechizo', reply_markup=get_start_keyboard())
                dynamo_db.delete(chat_id)
        elif chat_state == 'create_event':
            editing_status = chat_json['extra']['editing_status']

            if editing_status == 'event_title':
                event_title = msg.get('text', '')

                chat_json['extra']['event_data']['event_title'] = event_title
                chat_json['extra']['editing_status'] = None

                bot.sendMessage(chat_id, f'Se ha establecido el titulo {event_title}')

                bot.sendMessage(
                    chat_id,
                    TEMPLATE_EVENT.format(
                        event_title=chat_json['extra']['event_data'].get('event_title', ''),
                        event_date=chat_json['extra']['event_data'].get('event_date', ''),
                        event_time=chat_json['extra']['event_data'].get('event_time', ''),
                        event_address=chat_json['extra']['event_data'].get('event_address', ''),
                        event_master=chat_json['extra']['event_data'].get('event_master', ''),
                        event_free=chat_json['extra']['event_data'].get('event_players_limit', 0) - len(chat_json['extra']['event_data'].get('event_players', {})),
                        event_players=''.join([f'\n---{name}' for _, name in chat_json['extra']['event_data'].get('event_players', {}).items()])
                    ),
                    parse_mode='Markdown',
                    reply_markup=get_create_event_keyboard()
                )
                dynamo_db.set(chat_id, chat_json)
            elif editing_status == 'event_time':
                event_time = msg['text']
                match = re.search('[0-2][0-9]:[0-6][0-9]', event_time)

                if match:
                    chat_json['extra']['event_data']['event_time'] =event_time
                    chat_json['extra']['editing_status'] = None

                    bot.sendMessage(chat_id, f'Se ha establecido la hora a las {event_time}')

                    bot.sendMessage(
                        chat_id,
                        TEMPLATE_EVENT.format(
                            event_title=chat_json['extra']['event_data'].get('event_title', ''),
                            event_date=chat_json['extra']['event_data'].get('event_date', ''),
                            event_time=chat_json['extra']['event_data'].get('event_time', ''),
                            event_address=chat_json['extra']['event_data'].get('event_address', ''),
                            event_master=chat_json['extra']['event_data'].get('event_master', ''),
                            event_free=chat_json['extra']['event_data'].get('event_players_limit', 0) - len(chat_json['extra']['event_data'].get('event_players', {})),
                            event_players=''.join([f'\n---{name}' for _, name in chat_json['extra']['event_data'].get('event_players', {}).items()])
                        ),
                        parse_mode='Markdown',
                        reply_markup=get_create_event_keyboard()
                    )
                    dynamo_db.set(chat_id, chat_json)
                else:
                    bot.sendMessage(chat_id, f'El formato introducido no es correcto. Debe ser HH:MM.')
            elif editing_status == 'event_address':
                event_address = msg.get('text', '')

                chat_json['extra']['event_data']['event_address'] = event_address
                chat_json['extra']['editing_status'] = None

                bot.sendMessage(chat_id, f'Se ha establecido el lugar en {event_address}')

                bot.sendMessage(
                    chat_id,
                    TEMPLATE_EVENT.format(
                        event_title=chat_json['extra']['event_data'].get('event_title', ''),
                        event_date=chat_json['extra']['event_data'].get('event_date', ''),
                        event_time=chat_json['extra']['event_data'].get('event_time', ''),
                        event_address=chat_json['extra']['event_data'].get('event_address', ''),
                        event_master=chat_json['extra']['event_data'].get('event_master', ''),
                        event_free=chat_json['extra']['event_data'].get('event_players_limit', 0) - len(chat_json['extra']['event_data'].get('event_players', {})),
                        event_players=''.join([f'\n---{name}' for _, name in chat_json['extra']['event_data'].get('event_players', {}).items()])
                    ),
                    parse_mode='Markdown',
                    reply_markup=get_create_event_keyboard()
                )
                dynamo_db.set(chat_id, chat_json)
            elif editing_status == 'event_num_players':
                try:
                    event_num_players = int(msg.get('text'))
                except (ValueError, TypeError) as exc:
                    event_num_players = None

                if event_num_players is not None and event_num_players < 10:
                    chat_json['extra']['event_data']['event_players'] = {}
                    chat_json['extra']['event_data']['event_players_limit'] = event_num_players
                    chat_json['extra']['editing_status'] = None

                    bot.sendMessage(chat_id, f'Se ha establecido el número de jugadores en {event_num_players}')

                    bot.sendMessage(
                        chat_id,
                        TEMPLATE_EVENT.format(
                            event_title=chat_json['extra']['event_data'].get('event_title', ''),
                            event_date=chat_json['extra']['event_data'].get('event_date', ''),
                            event_time=chat_json['extra']['event_data'].get('event_time', ''),
                            event_address=chat_json['extra']['event_data'].get('event_address', ''),
                            event_master=chat_json['extra']['event_data'].get('event_master', ''),
                            event_free=chat_json['extra']['event_data'].get('event_players_limit', 0) - len(chat_json['extra']['event_data'].get('event_players', {})),
                            event_players=''.join([f'\n---{name}' for _, name in chat_json['extra']['event_data'].get('event_players', {}).items()])
                        ),
                        parse_mode='Markdown',
                        reply_markup=get_create_event_keyboard()
                    )
                    dynamo_db.set(chat_id, chat_json)
                else:
                    bot.sendMessage(chat_id, f'El valor introducido no es correcto. Debe ser un número entero menor a 10')


def process_callback(msg):
    """
    Method to process callback when button is pressed
    """
    chat_id = msg.get('message', {}).get('chat', {}).get('id')
    button_type, button_data = msg.get('data', '').split(':')

    logger.info(f'Press button: {button_type}, {button_data}')

    if button_type == 'start':
        dynamo_db.delete(chat_id)  # Reiniciamos estado de conversación

        if button_data == 'get_dice_roll':
            bot.sendMessage(chat_id, 'Introduce el tipo de dado que quieres lanzar', reply_markup=get_dices_keyboard())
        elif button_data == 'get_spell_info':
            bot.sendMessage(chat_id, 'Introduce el hechizo que quieres buscar')
            dynamo_db.set(chat_id, {'state': button_data, 'extra': {}})
        elif button_data == 'get_closest_events':
            bot.sendMessage(chat_id, 'Estos son los próximos eventos:')
            items = dynamo_db.get_calendar()
            print(items)
            for item in items:
                print(item.get('event_players', {}))
                bot.sendMessage(
                    chat_id,
                    TEMPLATE_EVENT.format(
                        event_title=item.get('event_title', ''),
                        event_date=item.get('event_date', ''),
                        event_time=item.get('event_time', ''),
                        event_address=item.get('event_address', ''),
                        event_master=item.get('event_master', ''),
                        event_free=item.get('event_players_limit', 0) - len(item.get('event_players', {})),
                        event_players=''.join([f'\n---{name}' for _, name in item.get('event_players', {}).items()])
                    ) + f"\n\n*Id:* {item.get('calendar_id', '')}",
                    parse_mode='Markdown'
                )
    elif button_type == 'roll_dice':
        bot.sendMessage(chat_id, 'Introduce el número de dados a lanzar')
        dynamo_db.set(chat_id, {'state': button_type, 'extra': {'dice_face': int(button_data)}})
    elif button_type == 'spell_type':
        chat_json = dynamo_db.get(chat_id)

        if chat_json:
            bot.sendMessage(chat_id, get_spell_type_sentence(button_data, chat_json.get('extra', {}).get('row')), reply_markup=get_start_keyboard())
            dynamo_db.delete(chat_id)
    elif button_type == 'calendar':
        chat_json = dynamo_db.get(chat_id)
        if chat_json:
            chat_state = chat_json.get('state')
            if chat_state == 'create_event':
                editing_status = chat_json['extra']['editing_status']
                if editing_status == 'event_date':
                    calendar = TelegramCalendar(bot, msg)
                    selected_date = calendar.process_calendar_selection(button_data)
                    if selected_date:
                        formatted_date = selected_date.strftime('%d/%m/%Y')

                        chat_json['extra']['event_data']['event_date'] = formatted_date
                        chat_json['extra']['editing_status'] = None

                        bot.sendMessage(chat_id, f'Se ha establecido la fecha {formatted_date}')

                        bot.sendMessage(
                            chat_id,
                            TEMPLATE_EVENT.format(
                                event_title=chat_json['extra']['event_data'].get('event_title', ''),
                                event_date=chat_json['extra']['event_data'].get('event_date', ''),
                                event_time=chat_json['extra']['event_data'].get('event_time', ''),
                                event_address=chat_json['extra']['event_data'].get('event_address', ''),
                                event_master=chat_json['extra']['event_data'].get('event_master', ''),
                                event_free=chat_json['extra']['event_data'].get('event_players_limit', 0) - len(chat_json['extra']['event_data'].get('event_players', {})),
                                event_players=''.join([f'\n---{name}' for _, name in chat_json['extra']['event_data'].get('event_players', {}).items()])
                            ),
                            parse_mode='Markdown',
                            reply_markup=get_create_event_keyboard()
                        )
                        dynamo_db.set(chat_id, chat_json)
    elif button_type == 'create_event':
        message_id = msg.get('message', {}).get('message_id')

        chat_json = dynamo_db.get(chat_id)
        if chat_json:
            if button_data == 'add_title':
                chat_json['extra']['editing_status'] = 'event_title'

                bot.editMessageText(
                    msg_identifier=(chat_id, message_id),
                    text='Introduce el título del evento',
                )

                dynamo_db.set(chat_id, chat_json)
            elif button_data == 'add_date':
                chat_json['extra']['editing_status'] = 'event_date'

                bot.editMessageText(
                    msg_identifier=(chat_id, message_id),
                    text='Introduce un día para el evento',
                    reply_markup=TelegramCalendar.create_calendar()
                )

                dynamo_db.set(chat_id, chat_json)
            elif button_data == 'add_time':
                chat_json['extra']['editing_status'] = 'event_time'

                bot.editMessageText(
                    msg_identifier=(chat_id, message_id),
                    text='Introduce la hora del evento en formato (HH:MM)',
                )

                dynamo_db.set(chat_id, chat_json)
            elif button_data == 'add_address':
                chat_json['extra']['editing_status'] = 'event_address'

                bot.editMessageText(
                    msg_identifier=(chat_id, message_id),
                    text='Introduce el lugar del evento',
                )

                dynamo_db.set(chat_id, chat_json)
            elif button_data == 'add_num_players':
                chat_json['extra']['editing_status'] = 'event_num_players'

                bot.editMessageText(
                    msg_identifier=(chat_id, message_id),
                    text='Introduce el numero de jugadores del evento',
                )

                dynamo_db.set(chat_id, chat_json)
            elif button_data == 'publish_event':
                event_date = chat_json['extra']['event_data'].get('event_date')
                event_time = chat_json['extra']['event_data'].get('event_time')

                if event_date and event_time:
                    key_datetime = datetime.strptime(f'{event_date}T{event_time}', '%d/%m/%YT%H:%M')
                elif event_date:
                    key_datetime = datetime.strptime(f'{event_date}', '%d/%m/%Y')
                else:
                    key_datetime = datetime.now()

                calendar_id = dynamo_db.set_calendar(key_datetime, {
                    'event_title': chat_json['extra']['event_data'].get('event_title', ''),
                    'event_date': chat_json['extra']['event_data'].get('event_date', ''),
                    'event_time': chat_json['extra']['event_data'].get('event_time', ''),
                    'event_address': chat_json['extra']['event_data'].get('event_address', ''),
                    'event_master': chat_json['extra']['event_data'].get('event_master', ''),
                    'event_players_limit': chat_json['extra']['event_data'].get('event_players_limit', 0),
                    'event_players': chat_json['extra']['event_data'].get('event_players', {})
                })

                bot.editMessageText(
                    msg_identifier=(chat_id, message_id),
                    text='Evento publicado correctamente',
                )

                bot.sendMessage(
                    chat_id,
                    TEMPLATE_EVENT.format(
                        event_title=chat_json['extra']['event_data'].get('event_title', ''),
                        event_date=chat_json['extra']['event_data'].get('event_date', ''),
                        event_time=chat_json['extra']['event_data'].get('event_time', ''),
                        event_address=chat_json['extra']['event_data'].get('event_address', ''),
                        event_master=chat_json['extra']['event_data'].get('event_master', ''),
                        event_free=chat_json['extra']['event_data'].get('event_players_limit', 0) - len(chat_json['extra']['event_data'].get('event_players', {})),
                        event_players=''.join([f'\n---{name}' for _, name in chat_json['extra']['event_data'].get('event_players', {}).items()])
                    ) + f"\n\n*Id:* {calendar_id}",
                    parse_mode='Markdown'
                )

                dynamo_db.delete(chat_id)
            elif button_data == 'cancel_event':
                bot.editMessageText(
                    msg_identifier=(chat_id, message_id),
                    text='Evento cancelado correctamente',
                )

                dynamo_db.delete(chat_id)


def is_start_cmd(msg):
    """
    Check if msg text is /start
    """
    return 'text' in msg and msg['text'] == '/start'


def is_help_cmd(msg):
    """
    Check if msg text is /help
    """
    return 'text' in msg and msg['text'] == '/help'


def is_create_event_cmd(msg):
    """
    Check if msg text is /create_event
    """
    return 'text' in msg and msg['text'] == '/create_event'


def is_join_event_cmd(msg):
    """
    Check if msg text is /join_event <event_id>
    """
    return 'text' in msg and msg['text'].startswith('/join_event')


def get_start_keyboard():
    keyboard = [
        [InlineKeyboardButton(text='Buscar Hechizo', callback_data=f'start:get_spell_info')],
        [InlineKeyboardButton(text='Tirar dados', callback_data=f'start:get_dice_roll')],
        [InlineKeyboardButton(text='Próximos eventos', callback_data=f'start:get_closest_events')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_dices_keyboard():
    keyboard = [
        [InlineKeyboardButton(text='d4', callback_data=f'roll_dice:4')],
        [InlineKeyboardButton(text='d6', callback_data=f'roll_dice:6')],
        [InlineKeyboardButton(text='d8', callback_data=f'roll_dice:8')],
        [InlineKeyboardButton(text='d10', callback_data=f'roll_dice:10')],
        [InlineKeyboardButton(text='d20', callback_data=f'roll_dice:20')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_spell_type_keyboard():
    keyboard = [
        [InlineKeyboardButton(text='Categoria', callback_data=f'spell_type:category')],
        [InlineKeyboardButton(text='Nivel', callback_data=f'spell_type:level')],
        [InlineKeyboardButton(text='Tiempo de Lanzamiento', callback_data=f'spell_type:spelling_time')],
        [InlineKeyboardButton(text='Alcance', callback_data=f'spell_type:distance')],
        [InlineKeyboardButton(text='Componentes', callback_data=f'spell_type:components')],
        [InlineKeyboardButton(text='Duración', callback_data=f'spell_type:duration')],
        [InlineKeyboardButton(text='Descripción', callback_data=f'spell_type:description')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_create_event_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(text='Titulo', callback_data=f'create_event:add_title'),
        ],
        [
            InlineKeyboardButton(text='Fecha', callback_data=f'create_event:add_date'),
            InlineKeyboardButton(text='Hora', callback_data=f'create_event:add_time'),
        ],
        [
            InlineKeyboardButton(text='Dirección', callback_data=f'create_event:add_address'),
            InlineKeyboardButton(text='N. Jugadores', callback_data=f'create_event:add_num_players'),
        ],
        [
            InlineKeyboardButton(text='Publicar', callback_data=f'create_event:publish_event'),
            InlineKeyboardButton(text='Cancelar', callback_data=f'create_event:cancel_event')
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


__all__ = ['flow']
