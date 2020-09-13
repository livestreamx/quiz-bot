from functools import cached_property

import telebot
from quiz_bot.quiz.objects import ApiCommand, SkipApprovalCommand


class UserMarkupMaker:
    @cached_property
    def _help_button(self) -> telebot.types.InlineKeyboardButton:
        return telebot.types.InlineKeyboardButton(text="Помощь", callback_data=ApiCommand.HELP.as_url)

    @cached_property
    def _start_button(self) -> telebot.types.InlineKeyboardButton:
        return telebot.types.InlineKeyboardButton(text="Старт", callback_data=ApiCommand.START.as_url)

    @cached_property
    def _status_button(self) -> telebot.types.InlineKeyboardButton:
        return telebot.types.InlineKeyboardButton(text="Статус", callback_data=ApiCommand.STATUS.as_url)

    @cached_property
    def _skip_button(self) -> telebot.types.InlineKeyboardButton:
        return telebot.types.InlineKeyboardButton(text="Пропустить вопрос!", callback_data=ApiCommand.SKIP.as_url)

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
    def skip_markup(self) -> telebot.types.InlineKeyboardMarkup:
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(self._skip_button)
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

    @cached_property
    def skip_approval_markup(self) -> telebot.types.InlineKeyboardMarkup:
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton(text="Да", callback_data=SkipApprovalCommand.YES),
            telebot.types.InlineKeyboardButton(text="Нет", callback_data=SkipApprovalCommand.NO),
        )
        return keyboard
