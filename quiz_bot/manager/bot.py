import collections
import logging
import threading
from types import FunctionType
from typing import Any, DefaultDict, List, Optional, cast
from uuid import uuid4

import requests
import telebot
import tenacity
from quiz_bot.clients import ChitchatClient, ChitchatPrewrittenDetectedError, ChitChatRequest
from quiz_bot.manager.challenge import ChallengeMaster
from quiz_bot.manager.errors import NotSupportedCallbackError
from quiz_bot.manager.interface import InterfaceMaker
from quiz_bot.manager.objects import ApiCommand, ContentType
from quiz_bot.settings import InfoSettings, LoggingSettings, RemoteClientSettings
from quiz_bot.storage import ContextUser, CorrectAnswerResult, IUserStorage

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

    def run(self) -> None:
        logger.info('Bot successfully started.')
        self._bot.polling(none_stop=True)

    @staticmethod
    def _make_unknown_user(user: telebot.types.User) -> ContextUser:
        return ContextUser(id=0, external_id=user.id, chitchat_id=str(uuid4()), first_name="<unknown>")

    def _register_handlers(self) -> None:  # noqa: C901
        @self._bot.message_handler(commands=[ApiCommand.HELP], content_types=[ContentType.TEXT])
        def help_handler(message: telebot.types.Message) -> None:
            logger.info('Got %s message from chat #%s', ApiCommand.START.name, message.chat.id)
            with self._locks[message.chat.id]:
                internal_user = self._user_storage.get_or_create_user(user=message.from_user)
                self._send_answer(
                    user=internal_user,
                    message=message,
                    answers=[self._info_settings.greetings],
                    markup=self._interface_maker.start_markup,
                )

        @self._bot.message_handler(commands=[ApiCommand.START], content_types=[ContentType.TEXT])
        def start_handler(message: telebot.types.Message) -> None:
            logger.info('Got %s message from chat #%s', ApiCommand.START.name, message.chat.id)
            with self._locks[message.chat.id]:
                internal_user = self._user_storage.get_or_create_user(message.from_user)
                first_question = self._challenge_master.start_challenge_for_user(internal_user)

                replies: List[str] = []
                if isinstance(first_question, CorrectAnswerResult):
                    replies.extend([self._challenge_master.start_info, first_question.reply])
                else:
                    chitchat_answer = self._get_chitchat_answer(user=internal_user, message=message)
                    replies.append(chitchat_answer)
                self._send_answer(user=internal_user, message=message, answers=replies)

        def _get_api_handler_by_callback(query_data: str) -> FunctionType:
            if query_data == ApiCommand.HELP.as_url:
                return cast(FunctionType, help_handler)
            if query_data == ApiCommand.START.as_url:
                return cast(FunctionType, start_handler)
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
                    logger.warning("Gotten message '%s' from unknown user: %s!", message.text, message.from_user)
                    self._reply_to_unknown_user(message=message)
                    return
                self._resolve_and_reply(user=internal_user, message=message)

        logger.info('Bot API handlers registered.')

    @tenacity.retry(
        reraise=True,
        retry=tenacity.retry_if_exception_type(requests.ConnectionError),
        stop=tenacity.stop_after_attempt(3),
        before_sleep=tenacity.before_sleep_log(logger, logger.level),
        after=tenacity.after_log(logger, logger.level),
    )
    def _send_answer(
        self,
        user: ContextUser,
        message: telebot.types.Message,
        answers: List[str],
        markup: Optional[telebot.types.InlineKeyboardMarkup] = None,
    ) -> None:
        for answer in answers:
            markup_to_send = None
            if answer == answers[-1]:
                markup_to_send = markup

            self._bot.send_message(
                chat_id=message.chat.id, text=answer, parse_mode='html', reply_markup=markup_to_send,
            )
        logger.info(
            'Chat ID %s with %s: [user] %s -> [bot] %s',
            message.chat.id,
            user.full_name,
            message.text,
            f"[{'; '.join(answers)}]",
        )

    def _get_chitchat_answer(self, user: ContextUser, message: telebot.types.Message) -> str:
        try:
            response = self._chitchat_client.make_request(
                data=ChitChatRequest(text=message.text, user_id=user.chitchat_id)
            )
            return response.text
        except requests.RequestException:
            logger.exception("Error while making request to chitchat!")
            return self._info_settings.random_empty_message
        except ChitchatPrewrittenDetectedError as e:
            logger.info(e)  # noqa: G200
            return self._info_settings.random_empty_message

    def _resolve_and_reply(self, user: ContextUser, message: telebot.types.Message) -> None:
        challenge_master_answer = self._challenge_master.get_answer_result(user=user, message=message)
        replies: List[str] = []
        if isinstance(challenge_master_answer, CorrectAnswerResult):
            replies.append(challenge_master_answer.reply)
        else:
            replies.append(self._get_chitchat_answer(user=user, message=message))
        if challenge_master_answer.post_reply is not None:
            replies.append(challenge_master_answer.post_reply)
        self._send_answer(user=user, message=message, answers=replies)

    def _reply_to_unknown_user(self, message: telebot.types.Message) -> None:
        unknown_user = self._make_unknown_user(message.from_user)
        chitchat_answer = self._get_chitchat_answer(user=unknown_user, message=message)
        self._send_answer(
            user=unknown_user,
            message=message,
            answers=[chitchat_answer, self._info_settings.unknown_info],
            markup=self._interface_maker.help_markup,
        )
