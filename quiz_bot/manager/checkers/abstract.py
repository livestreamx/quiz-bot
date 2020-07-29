import abc
import logging

import telebot
from quiz_bot.manager.objects import CheckedResult
from quiz_bot.storage import ContextChallenge, ContextResult, ContextUser, CurrentChallenge

logger = logging.getLogger(__name__)


class IResultChecker(abc.ABC):
    @abc.abstractmethod
    def prepare_user_result(self, user: ContextUser, challenge: ContextChallenge) -> ContextResult:
        pass

    @abc.abstractmethod
    def check_answer(
        self, user: ContextUser, current_challenge: CurrentChallenge, message: telebot.types.Message
    ) -> CheckedResult:
        pass

    @classmethod
    @abc.abstractmethod
    def _match(cls, answer: str, expectation: str) -> bool:
        pass
