import logging
from typing import Callable

import telebot
from quiz_bot.clients import BotResponse, RemoteBotClient, SendMessageError
from quiz_bot.quiz.errors import NotSupportedCallbackError
from quiz_bot.quiz.interfaces.base_interface import BaseInterface
from quiz_bot.quiz.manager import QuizManager
from quiz_bot.quiz.objects import ApiCommand, ContentType
from quiz_bot.storage import IMessageStorage

logger = logging.getLogger(__name__)


class QuizInterface(BaseInterface):
    def __init__(self, client: RemoteBotClient, manager: QuizManager, message_storage: IMessageStorage) -> None:
        super().__init__(client)
        self._manager = manager
        self._message_storage = message_storage

    def _process(self, message: telebot.types.Message, func: Callable[[telebot.types.Message], BotResponse]) -> None:
        logger.info("Got '%s' message from chat #%s", message.text, message.chat.id)
        with self._client.thread_lock[message.chat.id]:
            response = func(message)
            self._message_storage.save_all(response.replies)
            try:
                self._client.send(response)
            except SendMessageError:
                logger.exception(
                    "Could not sent reply for user '%s', chat ID '%s'!", message.from_user.username, message.chat.id
                )

    def _register_handlers(self, bot: telebot.TeleBot) -> None:  # noqa: C901
        @bot.message_handler(commands=[ApiCommand.HELP], content_types=[ContentType.TEXT])
        def help_handler(message: telebot.types.Message) -> None:
            self._process(message, func=self._manager.get_help_response)

        @bot.message_handler(commands=[ApiCommand.START], content_types=[ContentType.TEXT])
        def start_handler(message: telebot.types.Message) -> None:
            self._process(message, func=self._manager.get_start_response)

        @bot.message_handler(commands=[ApiCommand.STATUS], content_types=[ContentType.TEXT])
        def status_handler(message: telebot.types.Message) -> None:
            self._process(message, func=self._manager.get_status_response)

        @bot.message_handler(content_types=[ContentType.TEXT])
        def default_handler(message: telebot.types.Message) -> None:
            self._process(message, func=self._manager.respond)

        def skip_handler(message: telebot.types.Message) -> None:
            self._process(message, func=self._manager.get_skip_response)

        def _get_handler_by_data(data: str) -> Callable[[telebot.types.Message], BotResponse]:
            if data == ApiCommand.HELP.as_url:
                return help_handler  # type: ignore
            if data == ApiCommand.START.as_url:
                return start_handler  # type: ignore
            if data == ApiCommand.STATUS.as_url:
                return status_handler  # type: ignore
            if data.startswith(ApiCommand.SKIP.as_url):
                return skip_handler  # type: ignore
            raise NotSupportedCallbackError(f"Unsupported callback query data: {data}!")

        @bot.callback_query_handler(func=lambda _: True)
        def markup_callback(query: telebot.types.CallbackQuery) -> None:
            self._client.bot.answer_callback_query(query.id)
            query.message.text = query.data
            query.message.from_user = query.from_user
            _get_handler_by_data(query.data)(query.message)

        logger.info("QuizBot API handlers registered.")
