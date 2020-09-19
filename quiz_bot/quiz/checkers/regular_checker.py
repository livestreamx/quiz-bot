import logging
import re
from typing import Match, Optional, Set

import telebot
from quiz_bot.entity import CheckedResult, ContextChallenge, ContextParticipant, RegularChallengeInfo
from quiz_bot.quiz.checkers.base_checker import BaseResultChecker

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


class RegularResultChecker(BaseResultChecker[RegularChallengeInfo], AnswerMatchingMixin):
    def check_answer(
        self,
        participant: ContextParticipant,
        data: ContextChallenge,
        info: RegularChallengeInfo,
        message: telebot.types.Message,
    ) -> CheckedResult:
        current_result = self._result_storage.get_last_result(participant_id=participant.id)
        expectations = {self._replace_symbols(x) for x in info.get_answer_variants(current_result.phase)}
        if not self._match(answer=self._replace_symbols(message.text), expectations=expectations):
            logger.debug(
                "User '%s' given incorrect answer for phase %s, challenge %s",
                participant.user.nick_name,
                current_result.phase,
                data.id,
            )
            return CheckedResult(correct=False, finish_condition_reached=False, next_phase=current_result.phase)

        logger.info(
            "User '%s' given CORRECT answer for phase %s, challenge %s",
            participant.user.nick_name,
            current_result.phase,
            data.id,
        )
        return self._next_result(participant=participant, data=data, current_result=current_result,)
