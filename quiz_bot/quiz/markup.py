from functools import cached_property

import telebot
from quiz_bot.quiz.objects import ApiCommand


class UserMarkupMaker:
    @staticmethod
    def _add_start_button(keyboard: telebot.types.InlineKeyboardMarkup) -> None:
        keyboard.add(telebot.types.InlineKeyboardButton("Start", callback_data=ApiCommand.START.as_url))

    @staticmethod
    def _add_help_button(keyboard: telebot.types.InlineKeyboardMarkup) -> None:
        keyboard.add(telebot.types.InlineKeyboardButton("Help", callback_data=ApiCommand.HELP.as_url))

    @cached_property
    def start_markup(self) -> telebot.types.InlineKeyboardMarkup:
        keyboard = telebot.types.InlineKeyboardMarkup()
        self._add_start_button(keyboard)
        return keyboard

    @cached_property
    def help_markup(self) -> telebot.types.InlineKeyboardMarkup:
        keyboard = telebot.types.InlineKeyboardMarkup()
        self._add_help_button(keyboard)
        return keyboard
