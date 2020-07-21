from functools import cached_property
from types import FunctionType

import telebot

from manager.objects import ApiCommand


class InterfaceMaker:
    @staticmethod
    def _add_start_button(keyboard: telebot.types.InlineKeyboardMarkup) -> None:
        keyboard.add(telebot.types.InlineKeyboardButton("Start", callback_data=ApiCommand.START.as_url))

    @cached_property
    def start_markup(self) -> telebot.types.InlineKeyboardMarkup:
        keyboard = telebot.types.InlineKeyboardMarkup()
        self._add_start_button(keyboard)
        return keyboard

    @staticmethod
    def callback_from(bot: telebot.TeleBot, query: telebot.types.CallbackQuery, func: FunctionType) -> None:
        bot.answer_callback_query(query.id)
        query.message.text = query.data
        func(query.message)
