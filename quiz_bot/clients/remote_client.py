import collections
import logging
import threading
from typing import Any, DefaultDict, Dict, List, Optional

import requests
import telebot
import tenacity
from pydantic import BaseModel, root_validator
from quiz_bot.entity import ContextUser, RemoteClientSettings

logger = logging.getLogger(__name__)


class SendMessageError(RuntimeError):
    pass


class BotResponse(BaseModel):
    user: ContextUser
    user_message: Optional[str]
    reply: Optional[str]
    replies: List[str] = []
    split: bool = False
    markup: Optional[telebot.types.InlineKeyboardMarkup]

    @root_validator
    def make_replies(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        reply = values.get('reply')
        if isinstance(reply, str):
            values['replies'] = [reply]
        replies = values.get('replies')
        if not replies:
            raise ValueError("No one reply has been specified!")
        return values

    class Config:
        arbitrary_types_allowed = True


class RemoteBotClient:
    def __init__(self, settings: RemoteClientSettings) -> None:
        self._settings = settings
        self._locks: DefaultDict[Any, threading.Lock] = collections.defaultdict(threading.Lock)
        self._telebot = telebot.TeleBot(token=settings.token, num_threads=settings.threads_num)

    @property
    def bot(self) -> telebot.TeleBot:
        return self._telebot

    def run_loop(self) -> None:
        self._telebot.polling(none_stop=True, timeout=self._settings.poll_timeout)

    @property
    def thread_lock(self) -> DefaultDict[Any, threading.Lock]:
        return self._locks

    @staticmethod
    def _get_grouped_replies(answers: List[str], split_answers: bool) -> List[str]:
        if split_answers:
            return answers
        return [" ".join(answers)]

    @tenacity.retry(
        reraise=True,
        retry=tenacity.retry_if_exception_type(SendMessageError),
        stop=tenacity.stop_after_attempt(3),
        before_sleep=tenacity.before_sleep_log(logger, logger.level),
        after=tenacity.after_log(logger, logger.level),
    )
    def send(self, response: BotResponse) -> None:
        messages = self._get_grouped_replies(answers=response.replies, split_answers=response.split)
        for num, message in enumerate(messages, start=1):
            markup = None
            if num == len(messages):
                markup = response.markup

            try:
                self._telebot.send_message(
                    chat_id=response.user.remote_chat_id,
                    text=message,
                    parse_mode='html',
                    reply_markup=markup,
                    timeout=self._settings.read_timeout,
                )
            except (requests.ConnectionError, telebot.apihelper.ApiException) as e:
                logger.error("Catched error while trying to send message for chat ID %s!", response.user.remote_chat_id)
                raise SendMessageError from e
            logger.info(
                'Chat ID %s with %s: [user] %s -> [bot] %s',
                response.user.remote_chat_id,
                response.user.full_name,
                response.user_message,
                message,
            )
