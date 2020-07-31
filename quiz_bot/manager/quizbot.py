import logging
from types import FunctionType
from typing import cast

import requests
import telebot
from quiz_bot.clients import ChitchatClient, ChitchatPrewrittenDetectedError, ChitChatRequest, RemoteBotClient
from quiz_bot.entity import ContextUser, InfoSettings
from quiz_bot.manager.challenge import ChallengeMaster
from quiz_bot.manager.errors import NotSupportedCallbackError
from quiz_bot.manager.interface import InterfaceMaker
from quiz_bot.manager.objects import ApiCommand, ContentType
from quiz_bot.storage import IUserStorage

logger = logging.getLogger(__name__)


class QuizBot:
    def __init__(
        self,
        user_storage: IUserStorage,
        chitchat_client: ChitchatClient,
        remote_client: RemoteBotClient,
        info_settings: InfoSettings,
        interface_maker: InterfaceMaker,
        challenge_master: ChallengeMaster,
    ) -> None:
        self._remote_client = remote_client

        self._user_storage = user_storage
        self._chitchat_client = chitchat_client
        self._info_settings = info_settings
        self._interface_maker = interface_maker
        self._challenge_master = challenge_master

        self._register_handlers(remote_client.bot)

    def run(self) -> None:
        logger.info('QuizBot is started.')
        self._remote_client.run_loop()

    def _register_handlers(self, bot: telebot.TeleBot) -> None:  # noqa: C901
        @bot.message_handler(commands=[ApiCommand.HELP], content_types=[ContentType.TEXT])
        def help_handler(message: telebot.types.Message) -> None:
            logger.info('Got %s message from chat #%s', ApiCommand.START.name, message.chat.id)
            with self._remote_client.thread_lock[message.chat.id]:
                internal_user = self._user_storage.get_or_create_user(message)
                self._remote_client.send(
                    user=internal_user,
                    bot_answers=[self._info_settings.greetings],
                    user_message=message.text,
                    markup=self._interface_maker.start_markup,
                )

        @bot.message_handler(commands=[ApiCommand.START], content_types=[ContentType.TEXT])
        def start_handler(message: telebot.types.Message) -> None:
            logger.info('Got %s message from chat #%s', ApiCommand.START.name, message.chat.id)
            with self._remote_client.thread_lock[message.chat.id]:
                internal_user = self._user_storage.get_or_create_user(message)
                first_question = self._challenge_master.start_challenge_for_user(internal_user)

                if first_question.correct:
                    replies = first_question.replies
                else:
                    replies = [self._get_chitchat_answer(user=internal_user, message=message)]
                self._remote_client.send(
                    user=internal_user,
                    bot_answers=replies,
                    user_message=message.text,
                    split_answers=first_question.split_replies,
                )

        def _get_api_handler_by_callback(query_data: str) -> FunctionType:
            if query_data == ApiCommand.HELP.as_url:
                return cast(FunctionType, help_handler)
            if query_data == ApiCommand.START.as_url:
                return cast(FunctionType, start_handler)
            raise NotSupportedCallbackError(f"Unsupported callback query data: {query_data}")

        @bot.callback_query_handler(func=lambda _: True)
        def callback(query: telebot.types.CallbackQuery) -> None:
            self._interface_maker.callback_from(
                bot=self._remote_client.bot, query=query, func=_get_api_handler_by_callback(query.data)
            )

        @bot.message_handler(content_types=[ContentType.TEXT])
        def default_handler(message: telebot.types.Message) -> None:
            logger.info('Got message from chat #%s', message.chat.id)
            with self._remote_client.thread_lock[message.chat.id]:
                internal_user = self._user_storage.get_user(message.from_user)
                if internal_user is None:
                    logger.warning("Gotten message '%s' from unknown user: %s!", message.text, message.from_user)
                    self._reply_to_unknown_user(message=message)
                    return
                self._resolve_and_reply(user=internal_user, message=message)

        logger.info("QuizBot API handlers registered.")

    def _get_chitchat_answer(self, user: ContextUser, message: telebot.types.Message) -> str:
        if self._chitchat_client.enabled:
            try:
                response = self._chitchat_client.make_request(
                    data=ChitChatRequest(text=message.text, user_id=user.chitchat_id)
                )
                return response.text
            except requests.RequestException:
                logger.exception("Error while making request to chitchat!")
            except ChitchatPrewrittenDetectedError as e:
                logger.info(e)  # noqa: G200
        return self._info_settings.random_empty_message

    def _resolve_and_reply(self, user: ContextUser, message: telebot.types.Message) -> None:
        challenge_master_answer = self._challenge_master.get_answer_result(user=user, message=message)
        if not challenge_master_answer.correct:
            challenge_master_answer.replies.insert(0, self._get_chitchat_answer(user=user, message=message))
        self._remote_client.send(
            user=user,
            bot_answers=challenge_master_answer.replies,
            user_message=message.text,
            split_answers=challenge_master_answer.split_replies,
        )

    def _reply_to_unknown_user(self, message: telebot.types.Message) -> None:
        unknown_user = self._user_storage.make_unknown_context_user(message.from_user)
        chitchat_answer = self._get_chitchat_answer(user=unknown_user, message=message)
        self._remote_client.send(
            user=unknown_user,
            bot_answers=[chitchat_answer, self._info_settings.unknown_info],
            user_message=message.text,
            markup=self._interface_maker.help_markup,
        )
