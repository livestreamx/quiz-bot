import logging
import re
from typing import Optional, Sequence, Set

import telebot
from quiz_bot.entity import CheckedResult, ContextChallenge, ContextResult, ContextUser, ExtendedChallenge
from quiz_bot.quiz.checkers.base import BaseResultChecker
from quiz_bot.storage import NoResultFoundError
from quiz_bot.utils import get_now

logger = logging.getLogger(__name__)


class AnswerMatchingMixin:
    @staticmethod
    def _prepare_for_matching(text: str) -> str:
        return text.strip().lower()

    @classmethod
    def _search(cls, answer: str, expectation: str) -> Optional[re.Match[str]]:
        return re.search(rf"({cls._prepare_for_matching(expectation)})+", cls._prepare_for_matching(answer))

    @classmethod
    def _match(cls, answer: str, expectations: Set[str]) -> bool:
        return any(cls._search(answer, expectation) for expectation in expectations)


class ClassicResultChecker(AnswerMatchingMixin, BaseResultChecker):
    @staticmethod
    def _resolve_challenge_finish(challenge: ExtendedChallenge, results: Sequence[ContextResult]) -> bool:
        return bool(len(results) == challenge.data.winner_amount)

    def _set_phase_finished(self, result: ContextResult) -> None:
        result.finished_at = get_now()
        self._result_storage.finish_phase(result=result, finish_time=result.finished_at)

    def prepare_user_result(self, user: ContextUser, challenge: ContextChallenge) -> ContextResult:
        try:
            return self._result_storage.get_last_user_result_by_challenge(user=user, challenge=challenge)
        except NoResultFoundError:
            self._result_storage.create_result(user=user, challenge=challenge, phase=1)
            return self._result_storage.get_last_user_result_by_challenge(user=user, challenge=challenge)

    def check_answer(
        self, user: ContextUser, current_challenge: ExtendedChallenge, message: telebot.types.Message
    ) -> CheckedResult:
        current_result = self._result_storage.get_last_user_result_by_challenge(
            user=user, challenge=current_challenge.data
        )
        if current_challenge.data.finished_at is not None:
            logger.info(
                "Challenge ID %s is finished. Skip result checking for user @%s",
                current_challenge.number,
                user.nick_name,
            )
            if current_result.finished_at is None:
                logger.info(
                    "User '%s' given answer when challenge with ID %s is finished!",
                    user.nick_name,
                    current_challenge.number,
                )
                self._set_phase_finished(current_result)
                return CheckedResult(correct=False, finish_condition_reached=True)
            return CheckedResult(correct=False, finish_condition_reached=False)

        expectations = current_challenge.info.get_answer_variants(current_result.phase)
        if not self._match(answer=message.text, expectations=expectations):
            logger.info(
                "User '%s' given incorrect answer for phase %s, challenge %s",
                user.nick_name,
                current_result.phase,
                current_challenge.number,
            )
            return CheckedResult(correct=False, finish_condition_reached=False, next_phase=current_result.phase)

        logger.info(
            "User '%s' given CORRECT answer for phase %s, challenge %s",
            user.nick_name,
            current_result.phase,
            current_challenge.number,
        )
        self._set_phase_finished(current_result)
        if current_result.phase == current_challenge.data.phase_amount:
            logger.info("User '%s' reached the end of challenge '%s!'", user.nick_name, current_challenge.info.name)
            equal_results = self._result_storage.get_equal_results(current_result)
            challenge_finished = self._resolve_challenge_finish(challenge=current_challenge, results=equal_results)
            return CheckedResult(correct=True, finish_condition_reached=challenge_finished)

        next_phase = current_result.phase + 1
        self._result_storage.prepare_next_result(result=current_result, next_phase=next_phase)
        return CheckedResult(correct=True, finish_condition_reached=False, next_phase=next_phase)
