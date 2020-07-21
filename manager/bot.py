import collections
import logging
import threading
from typing import Any, DefaultDict, Mapping, Optional
from uuid import uuid4

import requests
import telebot
from storage import ContextUser, IUserStorage

from manager.chitchat import ChitchatClient, ChitChatRequest
from manager.interface import InterfaceMaker
from manager.objects import ApiCommand, ContentType
from manager.settings import DialogSettings, LoggingSettings, RemoteClientSettings

logger = logging.getLogger(__name__)


class Bot:
    def __init__(
        self,
        user_storage: IUserStorage,
        chitchat_client: ChitchatClient,
        logging_settings: LoggingSettings,
        remote_client_settings: RemoteClientSettings,
        dialog_settings: DialogSettings,
        interface_maker: InterfaceMaker,
    ) -> None:
        self._locks: DefaultDict[Any, threading.Lock] = collections.defaultdict(threading.Lock)
        self._bot = telebot.TeleBot(remote_client_settings.api_key)

        self._user_storage = user_storage
        self._chitchat_client = chitchat_client
        self._logging_settings = logging_settings
        self._dialog_settings = dialog_settings
        self._interface_maker = interface_maker

        self._register_handlers()

        self._api_cmd_to_bot_answer_mapping: Mapping[str, str] = {
            ApiCommand.START.as_url: self._dialog_settings.start_info,
            ApiCommand.HELP.as_url: self._dialog_settings.greetings,
        }

    def run(self) -> None:
        logger.info('Bot successfully started.')
        self._bot.polling(none_stop=True)

    @staticmethod
    def _make_unknown_user(user: telebot.types.User) -> ContextUser:
        return ContextUser(id=0, external_id=user.id, chitchat_id=str(uuid4()), first_name="<unknown>")

    def _get_markup_for_api_cmd(self, message: telebot.types.Message) -> Optional[telebot.types.InlineKeyboardMarkup]:
        if message.text == ApiCommand.HELP.as_url:
            return self._interface_maker.start_markup
        return None

    def _register_handlers(self) -> None:
        @self._bot.message_handler(commands=[ApiCommand.START, ApiCommand.HELP], content_types=[ContentType.TEXT])
        def api_handler(message: telebot.types.Message) -> None:
            logger.info('Got %s message from chat #%s', ApiCommand.START.name, message.chat.id)
            with self._locks[message.chat.id]:
                internal_user = self._user_storage.get_or_create_user(user=message.from_user)
                self._send_answer(
                    user=internal_user,
                    message=message,
                    answer=self._api_cmd_to_bot_answer_mapping[message.text],
                    markup=self._get_markup_for_api_cmd(message),
                )

        @self._bot.callback_query_handler(func=lambda _: True)
        def callback(query: telebot.types.CallbackQuery) -> None:
            self._interface_maker.callback_from(bot=self._bot, query=query, func=api_handler)

        @self._bot.message_handler(content_types=[ContentType.TEXT])
        def default_handler(message: telebot.types.Message) -> None:
            logger.info('Got message from chat #%s', message.chat.id)
            with self._locks[message.chat.id]:
                internal_user = self._user_storage.get_user(message.from_user)
                if internal_user is None:
                    logger.warning("Gotten message from unknown user: %s!", message)
                    self._send_answer(
                        user=self._make_unknown_user(message.from_user),
                        message=message,
                        answer=self._dialog_settings.unknown_warning,
                    )
                    return
                chitchat_answer = self._get_chitchat_answer(user=internal_user, message=message)
                self._send_answer(user=internal_user, message=message, answer=chitchat_answer)

        logger.info('Bot API handlers registered.')

    def _send_answer(
        self,
        user: ContextUser,
        message: telebot.types.Message,
        answer: str,
        markup: Optional[telebot.types.InlineKeyboardMarkup] = None,
    ) -> None:
        self._bot.send_message(
            chat_id=message.chat.id, text=answer, parse_mode='html', reply_markup=markup,
        )
        logger.info(
            'Chat ID %s with %s: [user] %s -> [bot] %s', message.chat.id, user.full_name, message.text, answer,
        )

    def _get_chitchat_answer(self, user: ContextUser, message: telebot.types.Message) -> str:
        try:
            response = self._chitchat_client.make_request(
                data=ChitChatRequest(text=message.text, user_id=user.chitchat_id)
            )
            return response.text
        except requests.RequestException:
            logger.exception("Error while making request to chitchat!")
            return self._dialog_settings.empty_message
