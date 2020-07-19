import collections
import enum
import logging
import threading
from typing import Any, DefaultDict

import requests
import telebot
from storage import IUserStorage, User

from manager.chitchat import ChitchatClient
from manager.models import ChitChatRequest
from manager.settings import DialogSettings, LoggingSettings, RemoteClientSettings

logger = logging.getLogger(__name__)


class ApiCommand(str, enum.Enum):
    START = 'start'


class ContentType(str, enum.Enum):
    TEXT = 'text'


class Bot:
    def __init__(
        self,
        user_storage: IUserStorage,
        chitchat_client: ChitchatClient,
        logging_settings: LoggingSettings,
        remote_client_settings: RemoteClientSettings,
        dialog_settings: DialogSettings,
    ) -> None:
        self._locks: DefaultDict[Any, threading.Lock] = collections.defaultdict(threading.Lock)
        self._bot = telebot.TeleBot(remote_client_settings.api_key)

        self._user_storage = user_storage
        self._chitchat_client = chitchat_client
        self._logging_settings = logging_settings
        self._dialog_settings = dialog_settings

        self._register_handlers()

    def run(self) -> None:
        logger.info('Bot successfully started.')
        self._bot.polling(none_stop=True)

    def _register_handlers(self) -> None:
        @self._bot.message_handler(commands=[ApiCommand.START], content_types=[ContentType.TEXT])
        def _start_handler(message: telebot.types.Message) -> None:
            logger.info('Got %s message from chat #%s', ApiCommand.START.name, message.chat.id)
            with self._locks[message.chat.id]:
                internal_user = self._user_storage.get_or_create_user(user=message.from_user)
                self._send_answer(user=internal_user, message=message, answer=self._dialog_settings.greetings)

        @self._bot.message_handler(content_types=[ContentType.TEXT])
        def _default_handler(message: telebot.types.Message) -> None:
            logger.info('Got message from chat #%s', message.chat.id)
            with self._locks[message.chat.id]:
                internal_user = self._user_storage.get_user_by_external_id(message.from_user.id)
                if internal_user is None:
                    logger.warning("Gotten message from unknown user: %s!", message)
                    return
                chitchat_answer = self._get_chitchat_answer(user=internal_user, message=message)
                self._send_answer(user=internal_user, message=message, answer=chitchat_answer)

        logger.info('Bot API handlers registered.')

    def _send_answer(self, user: User, message: telebot.types.Message, answer: str) -> None:
        self._bot.send_message(chat_id=message.chat.id, text=answer, parse_mode='html')
        logger.info(
            'Chat ID %s with %s: [user] %s -> [bot] %s', message.chat.id, user.full_name, message.text, answer,
        )

    def _get_chitchat_answer(self, user: User, message: telebot.types.Message) -> str:
        try:
            response = self._chitchat_client.make_request(
                data=ChitChatRequest(text=message.text, user_id=user.chitchat_id)
            )
            return response.text
        except requests.RequestException:
            logger.exception("Error while making request to chitchat!")
            return self._dialog_settings.empty_message
