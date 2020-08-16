import abc
import logging
from typing import List

import telebot
from quiz_bot.entity import CheckedResult, ContextChallenge, ContextResult, ContextUser, ExtendedChallenge, WinnerResult

logger = logging.getLogger(__name__)


class IResultChecker(abc.ABC):
    @abc.abstractmethod
    def prepare_user_result(self, user: ContextUser, challenge: ContextChallenge) -> ContextResult:
        pass

    @abc.abstractmethod
    def check_answer(
        self, user: ContextUser, current_challenge: ExtendedChallenge, message: telebot.types.Message
    ) -> CheckedResult:
        pass

    @abc.abstractmethod
    def get_winners(self, challenge: ContextChallenge) -> List[WinnerResult]:
        pass
