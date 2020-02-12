#!/usr/bin/env python3
#
# A library that allows to create an inline calendar keyboard.
# grcanosa https://github.com/grcanosa
#
"""
Base methods for calendar keyboard creation and processing.
"""


from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
import datetime
import calendar


def create_callback_data(action, year, month, day):
    """ Create the callback data associated to each button"""
    return f'calendar:{";".join([action, str(year), str(month), str(day)])}'


def separate_callback_data(data):
    """ Separate the callback data"""
    return data.split(";")


class TelegramCalendar:
    def __init__(self, bot, msg):
        self.bot = bot
        self.msg = msg

        self.message_id = msg.get('message', {}).get('message_id')
        self.chat_id = msg.get('message', {}).get('chat', {}).get('id')
        self.text = msg.get('message', {}).get('text')

    @staticmethod
    def create_calendar(year=None, month=None):
        """
        Create an inline keyboard with the provided year and month
        :param int year: Year to use in the calendar, if None the current year is used.
        :param int month: Month to use in the calendar, if None the current month is used.
        :return: Returns the InlineKeyboardMarkup object with the calendar.
        """
        now = datetime.datetime.now()

        if not year:
            year = now.year

        if not month:
            month = now.month

        data_ignore = create_callback_data("IGNORE", year, month, 0)
        keyboard = []

        # First row - Month and Year
        row = list()
        row.append(InlineKeyboardButton(text=f'{calendar.month_name[month]} {year}', callback_data=data_ignore))
        keyboard.append(row)

        # Second row - Week Days
        row = list()
        for day in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
            row.append(InlineKeyboardButton(text=str(day), callback_data=data_ignore))

        keyboard.append(row)

        my_calendar = calendar.monthcalendar(year, month)
        for week in my_calendar:
            row = list()
            for day in week:
                if day == 0:
                    row.append(InlineKeyboardButton(text=" ", callback_data=data_ignore))
                else:
                    row.append(InlineKeyboardButton(text=str(day), callback_data=create_callback_data("DAY", year, month, day)))
            keyboard.append(row)

        # Last row - Buttons
        row = list()
        row.append(InlineKeyboardButton(text="<", callback_data=create_callback_data("PREV-MONTH", year, month, day)))
        row.append(InlineKeyboardButton(text=" ", callback_data=data_ignore))
        row.append(InlineKeyboardButton(text=">", callback_data=create_callback_data("NEXT-MONTH", year, month, day)))
        keyboard.append(row)

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    def process_calendar_selection(self, data):
        """
        Process the callback_query. This method generates a new calendar if forward or
        backward is pressed. This method should be called inside a CallbackQueryHandler.
        :param telegram.Bot bot: The bot, as provided by the CallbackQueryHandler
        :param telegram.Update update: The update, as provided by the CallbackQueryHandler
        :return: Returns a tuple (Boolean,datetime.datetime), indicating if a date is selected
                    and returning the date if so.
        """
        action, year, month, day = separate_callback_data(data)
        current = datetime.datetime(int(year), int(month), 1)

        if action == "DAY":
            return datetime.datetime(int(year), int(month), int(day))
        elif action == "PREV-MONTH":
            last_month = current - datetime.timedelta(days=1)
            self.bot.editMessageText(
                msg_identifier=(self.chat_id, self.message_id),
                text=self.text,
                reply_markup=self.create_calendar(int(last_month.year), int(last_month.month))
            )
        elif action == "NEXT-MONTH":
            next_month = current + datetime.timedelta(days=31)
            self.bot.editMessageText(
                msg_identifier=(self.chat_id, self.message_id),
                text=self.text,
                reply_markup=self.create_calendar(int(next_month.year), int(next_month.month))
            )
