import logging
import re
from typing import Match, Optional, Set

import telebot
from quiz_bot.entity import CheckedResult, ContextParticipant, ExtendedChallenge
from quiz_bot.quiz.checkers.base import BaseResultChecker

logger = logging.getLogger(__name__)


class AnswerMatchingMixin:
    @staticmethod
    def _prepare_for_matching(text: str) -> str:
        return text.strip().lower()

    @classmethod
    def _search(cls, answer: str, expectation: str) -> Optional[Match[str]]:
        return re.search(rf"({cls._prepare_for_matching(expectation)})+", cls._prepare_for_matching(answer))

    @classmethod
    def _match(cls, answer: str, expectations: Set[str]) -> bool:
        return any(cls._search(answer, expectation) for expectation in expectations)


class ClassicResultChecker(BaseResultChecker, AnswerMatchingMixin):
    def check_answer(
        self, participant: ContextParticipant, current_challenge: ExtendedChallenge, message: telebot.types.Message
    ) -> CheckedResult:
        current_result = self._result_storage.get_last_result(participant_id=participant.id)
        expectations = current_challenge.info.get_answer_variants(current_result.phase)
        if not self._match(answer=message.text, expectations=expectations):
            logger.info(
                "User '%s' given incorrect answer for phase %s, challenge %s",
                participant.user.nick_name,
                current_result.phase,
                current_challenge.number,
            )
            return CheckedResult(correct=False, finish_condition_reached=False, next_phase=current_result.phase)

        logger.info(
            "User '%s' given CORRECT answer for phase %s, challenge %s",
            participant.user.nick_name,
            current_result.phase,
            current_challenge.number,
        )
        self._set_phase_finished(current_result)
        if current_result.phase == current_challenge.data.phase_amount:
            return CheckedResult(correct=True)

        next_phase = current_result.phase + 1
        self._result_storage.create_result(participant_id=participant.id, phase=next_phase)
        return CheckedResult(correct=True, next_phase=next_phase)
