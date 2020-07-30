import collections
import logging
import threading
from typing import Any, DefaultDict, List, Optional

import requests
import telebot
import tenacity
from quiz_bot.settings import RemoteClientSettings
from quiz_bot.storage import ContextUser

logger = logging.getLogger(__name__)


class RemoteBotClient:
    def __init__(self, settings: RemoteClientSettings) -> None:
        self._locks: DefaultDict[Any, threading.Lock] = collections.defaultdict(threading.Lock)
        self._telebot = telebot.TeleBot(token=settings.token, num_threads=settings.threads_num)

    @property
    def bot(self) -> telebot.TeleBot:
        return self._telebot

    def run_loop(self) -> None:
        self._telebot.polling(none_stop=True)

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
        retry=tenacity.retry_if_exception_type(requests.ConnectionError),
        stop=tenacity.stop_after_attempt(3),
        before_sleep=tenacity.before_sleep_log(logger, logger.level),
        after=tenacity.after_log(logger, logger.level),
    )
    def send(
        self,
        user: ContextUser,
        message: telebot.types.Message,
        answers: List[str],
        split_answers: bool = False,
        markup: Optional[telebot.types.InlineKeyboardMarkup] = None,
    ) -> None:
        for reply in self._get_grouped_replies(answers=answers, split_answers=split_answers):
            self._telebot.send_message(chat_id=message.chat.id, text=reply, parse_mode='html', reply_markup=markup)
            logger.info(
                'Chat ID %s with %s: [user] %s -> [bot] %s', message.chat.id, user.full_name, message.text, reply,
            )
