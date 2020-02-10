import logging

import telepot
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton


from settings import *
from dynamo_db import dynamo_db
from messages import START_MSG, HELP_MSG
from dice_roll import get_dice_roll
from spell_info.pool import sqlite_db
from spell_info.utils import get_spell_type_sentence


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
        else:
            process_text(msg)
    elif flavor == 'callback_query':
        process_callback(msg)


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


def process_callback(msg):
    """
    Method to process callback when button is pressed
    """
    chat_id = msg.get('message').get('chat', {}).get('id')
    button_type, button_data = msg.get('data', '').split(':')

    logger.info(f'Press button: {button_type}, {button_data}')

    if button_type == 'start':
        dynamo_db.delete(chat_id)  # Reiniciamos estado de conversación

        if button_data == 'get_dice_roll':
            bot.sendMessage(chat_id, 'Introduce el tipo de dado que quieres lanzar', reply_markup=get_dices_keyboard())
        elif button_data == 'get_spell_info':
            bot.sendMessage(chat_id, 'Introduce el hechizo que quieres buscar')
            dynamo_db.set(chat_id, {'state': button_data, 'extra': {}})
    elif button_type == 'roll_dice':
        bot.sendMessage(chat_id, 'Introduce el número de dados a lanzar')
        dynamo_db.set(chat_id, {'state': button_type, 'extra': {'dice_face': int(button_data)}})
    elif button_type == 'spell_type':
        chat_json = dynamo_db.get(chat_id)

        if chat_json:
            bot.sendMessage(chat_id, get_spell_type_sentence(button_data, chat_json.get('extra', {}).get('row')), reply_markup=get_start_keyboard())
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


def get_start_keyboard():
    keyboard = [
        [InlineKeyboardButton(text='Buscar Hechizo', callback_data=f'start:get_spell_info')],
        [InlineKeyboardButton(text='Tirar dados', callback_data=f'start:get_dice_roll')],
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


__all__ = ['flow']
