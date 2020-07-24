import collections
import logging
import threading
from types import FunctionType
from typing import Any, DefaultDict, Optional
from uuid import uuid4

import requests
import telebot
from quiz_bot.manager.challenge import ChallengeMaster
from quiz_bot.manager.chitchat import ChitchatClient, ChitChatRequest
from quiz_bot.manager.errors import NotSupportedCallbackError
from quiz_bot.manager.interface import InterfaceMaker
from quiz_bot.manager.objects import ApiCommand, ContentType
from quiz_bot.settings import InfoSettings, LoggingSettings, RemoteClientSettings
from quiz_bot.storage import ContextUser, IUserStorage

logger = logging.getLogger(__name__)


class Bot:
    def __init__(
        self,
        user_storage: IUserStorage,
        chitchat_client: ChitchatClient,
        logging_settings: LoggingSettings,
        remote_client_settings: RemoteClientSettings,
        info_settings: InfoSettings,
        interface_maker: InterfaceMaker,
        challenge_master: ChallengeMaster,
    ) -> None:
        self._locks: DefaultDict[Any, threading.Lock] = collections.defaultdict(threading.Lock)
        self._bot = telebot.TeleBot(remote_client_settings.api_key)

        self._user_storage = user_storage
        self._chitchat_client = chitchat_client
        self._logging_settings = logging_settings
        self._info_settings = info_settings
        self._interface_maker = interface_maker
        self._challenge_master = challenge_master

        self._register_handlers()
        self._challenge_master.start_next_challenge()

    def run(self) -> None:
        logger.info('Bot successfully started.')
        self._bot.polling(none_stop=True)

    @staticmethod
    def _make_unknown_user(user: telebot.types.User) -> ContextUser:
        return ContextUser(id=0, external_id=user.id, chitchat_id=str(uuid4()), first_name="<unknown>")

    def _resolve_bot_answer(self, user: ContextUser, message: telebot.types.Message) -> str:
        challenge_master_answer = self._challenge_master.get_answer_result(user=user, message=message)
        if challenge_master_answer.correct:
            return challenge_master_answer.reply
        return self._get_chitchat_answer(user=user, message=message)

    def _register_handlers(self) -> None:
        @self._bot.message_handler(commands=[ApiCommand.HELP], content_types=[ContentType.TEXT])
        def help_handler(message: telebot.types.Message) -> None:
            logger.info('Got %s message from chat #%s', ApiCommand.START.name, message.chat.id)
            with self._locks[message.chat.id]:
                internal_user = self._user_storage.get_or_create_user(user=message.from_user)
                self._send_answer(
                    user=internal_user,
                    message=message,
                    answer=self._info_settings.greetings,
                    markup=self._interface_maker.start_markup,
                )

        @self._bot.message_handler(commands=[ApiCommand.START], content_types=[ContentType.TEXT])
        def start_handler(message: telebot.types.Message) -> None:
            logger.info('Got %s message from chat #%s', ApiCommand.START.name, message.chat.id)
            with self._locks[message.chat.id]:
                internal_user = self._user_storage.get_or_create_user(user=message.from_user)
                self._send_answer(
                    user=internal_user, message=message, answer=self._challenge_master.start_info,
                )

        def _get_api_handler_by_callback(query_data: str) -> FunctionType:
            if query_data == ApiCommand.START.as_url:
                return start_handler
            raise NotSupportedCallbackError(f"Unsupported callback query data: {query_data}")

        @self._bot.callback_query_handler(func=lambda _: True)
        def callback(query: telebot.types.CallbackQuery) -> None:
            self._interface_maker.callback_from(
                bot=self._bot, query=query, func=_get_api_handler_by_callback(query.data)
            )

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
                        answer=self._info_settings.unknown_info,
                    )
                    return
                bot_answer = self._resolve_bot_answer(user=internal_user, message=message)
                self._send_answer(user=internal_user, message=message, answer=bot_answer)

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
            return self._info_settings.empty_message
