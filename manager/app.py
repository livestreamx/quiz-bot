import collections
import logging
import threading
from typing import Any, DefaultDict, cast

import requests
import telebot
import tenacity

from manager.models import ChitChatRequest, ChitChatResponse
from manager.settings import ApplicationSettings, ChitchatClientSettings, RemoteClientSettings

logger = logging.getLogger(__name__)

_EMPTY_MSG_SMILE = r'¯\_(ツ)_/¯'
_DEFAULT_USER_ID = '<unknown>'


def get_full_name(user: telebot.types.User) -> str:
    """
    Get full name of the Telegram user in the form `<First Name> <Last Name> @<Username>`

    Args:
        user: Telegram user object

    Returns:
        String with a full name
    """
    name = user.first_name or ''
    if user.last_name:
        name += f' {user.last_name}'
    if user.username:
        name += f' @{user.username}'
    return name


def _create_bot(  # noqa: C901
    app_settings: ApplicationSettings,
    chitchat_settings: ChitchatClientSettings,
    remote_client_settings: RemoteClientSettings,
) -> telebot.TeleBot:
    locks: DefaultDict[Any, threading.Lock] = collections.defaultdict(threading.Lock)
    bot = telebot.TeleBot(remote_client_settings.api_key)

    @bot.message_handler(commands=['start'])
    def _start(message: telebot.types.Message) -> None:
        """
        Send response to a Telegram user `/start` command
        """
        with locks[message.chat.id]:
            _send(message, response=ChitChatResponse(text='Начнем?'))

    def _send(message: telebot.types.Message, response: ChitChatResponse) -> None:
        bot.send_message(chat_id=message.chat.id, text=response.text, parse_mode='html')

        logger.info(
            'Chat %s with %s: %s -> %s', message.chat.id, get_full_name(message.from_user), message.text, response
        )

    @tenacity.retry(
        reraise=True,
        retry=tenacity.retry_if_exception_type(requests.RequestException),
        stop=tenacity.stop_after_attempt(3),
        before_sleep=tenacity.before_sleep_log(logger, app_settings.log_level),
        after=tenacity.after_log(logger, app_settings.log_level),
    )
    def _get_response(text: str, user_id: str) -> ChitChatResponse:
        response = requests.post(
            chitchat_settings.url.human_repr(),
            json=ChitChatRequest(text=text, user_id=user_id).dict(),
            timeout=chitchat_settings.read_timeout,
        )
        response.raise_for_status()
        return ChitChatResponse.parse_obj(response.json())

    def _get_user_id(message: telebot.types.Message) -> str:
        if message.from_user:
            return cast(str, message.from_user.id)
        return _DEFAULT_USER_ID

    def _send_response(message: telebot.types.Message) -> None:
        """
        Send response to a Telegram user chat message.
        """
        chat_id = message.chat.id
        user_id = _get_user_id(message)

        with locks[chat_id]:
            try:
                response = _get_response(text=message.text, user_id=user_id)
            except requests.RequestException:
                logger.exception("Error while processing response!")
                response = ChitChatResponse(text=f"Ответа нет {_EMPTY_MSG_SMILE}")
            _send(message, response=response)

    @bot.message_handler()
    def send_response(message: telebot.types.Message) -> None:
        try:
            _send_response(message)
        except Exception:
            logger.exception("Error while trying to send response to remote chat!")

    return bot  # noqa: R504


def init_app(settings: ApplicationSettings) -> telebot.TeleBot:
    chitchat_client_settings = ChitchatClientSettings()
    remote_client_settings = RemoteClientSettings()
    return _create_bot(
        app_settings=settings, chitchat_settings=chitchat_client_settings, remote_client_settings=remote_client_settings
    )


def run_app(bot: telebot.TeleBot) -> None:
    logger.info('Telegram bot started')
    bot.polling(none_stop=True)
