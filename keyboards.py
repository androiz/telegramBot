from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton


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
