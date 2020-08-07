from functools import cached_property

import telebot
from quiz_bot.quiz.objects import ApiCommand


class UserMarkupMaker:
    @cached_property
    def _help_button(self) -> telebot.types.InlineKeyboardButton:
        return telebot.types.InlineKeyboardButton(text="Help", callback_data=ApiCommand.HELP.as_url)

    @cached_property
    def _start_button(self) -> telebot.types.InlineKeyboardButton:
        return telebot.types.InlineKeyboardButton(text="Start", callback_data=ApiCommand.START.as_url)

    @cached_property
    def _status_button(self) -> telebot.types.InlineKeyboardButton:
        return telebot.types.InlineKeyboardButton(text="Status", callback_data=ApiCommand.STATUS.as_url)

    @cached_property
    def help_markup(self) -> telebot.types.InlineKeyboardMarkup:
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(self._help_button)
        return keyboard

    @cached_property
    def start_markup(self) -> telebot.types.InlineKeyboardMarkup:
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(self._start_button)
        return keyboard

    @cached_property
    def status_markup(self) -> telebot.types.InlineKeyboardMarkup:
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(self._status_button)
        return keyboard

    @cached_property
    def start_with_status_markup(self) -> telebot.types.InlineKeyboardMarkup:
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(self._status_button, self._start_button)
        return keyboard

    @cached_property
    def start_with_help_markup(self) -> telebot.types.InlineKeyboardMarkup:
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(self._help_button, self._start_button)
        return keyboard
