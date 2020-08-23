import abc
import logging

import telebot
from quiz_bot.entity import CheckedResult, ContextParticipant, ContextResult, ExtendedChallenge

logger = logging.getLogger(__name__)


class IResultChecker(abc.ABC):
    @abc.abstractmethod
    def create_initial_phase(self, participant: ContextParticipant) -> ContextResult:
        pass

    @abc.abstractmethod
    def check_answer(
        self, participant: ContextParticipant, current_challenge: ExtendedChallenge, message: telebot.types.Message
    ) -> CheckedResult:
        pass

    @abc.abstractmethod
    def skip_question(self, participant: ContextParticipant, current_challenge: ExtendedChallenge) -> CheckedResult:
        pass
