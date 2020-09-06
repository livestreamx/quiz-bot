import abc
import logging
from typing import Generic

import telebot
from quiz_bot.entity import CheckedResult, ContextChallenge, ContextParticipant, ContextResult, TChallengeInfo

logger = logging.getLogger(__name__)


class IResultChecker(abc.ABC, Generic[TChallengeInfo]):
    @abc.abstractmethod
    def create_initial_phase(self, participant: ContextParticipant) -> ContextResult:
        pass

    @abc.abstractmethod
    def check_answer(
        self,
        participant: ContextParticipant,
        data: ContextChallenge,
        info: TChallengeInfo,
        message: telebot.types.Message,
    ) -> CheckedResult:
        pass

    @abc.abstractmethod
    def skip_question(self, participant: ContextParticipant, data: ContextChallenge,) -> CheckedResult:
        pass
