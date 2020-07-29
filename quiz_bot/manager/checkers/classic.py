import logging
import re
from typing import Sequence

import telebot
from quiz_bot.manager.checkers.base import BaseResultChecker
from quiz_bot.manager.objects import CheckedResult
from quiz_bot.storage import ContextChallenge, ContextResult, ContextUser, CurrentChallenge
from quiz_bot.utils import get_now

logger = logging.getLogger(__name__)


class AnswerMatchingMixin:
    @staticmethod
    def _prepare_for_matching(text: str) -> str:
        return text.strip().lower()

    @classmethod
    def _match(cls, answer: str, expectation: str) -> bool:
        return bool(re.search(rf"({cls._prepare_for_matching(expectation)})+", cls._prepare_for_matching(answer)))


class ClassicResultChecker(AnswerMatchingMixin, BaseResultChecker):
    @staticmethod
    def _resolve_challenge_finish(challenge: CurrentChallenge, results: Sequence[ContextResult]) -> bool:
        return bool(len(results) == challenge.data.winner_amount)

    def prepare_user_result(self, user: ContextUser, challenge: ContextChallenge) -> ContextResult:
        self._result_storage.create_result(user=user, challenge=challenge, phase=1)
        return self._result_storage.get_last_result(user=user, challenge=challenge)

    def check_answer(
        self, user: ContextUser, current_challenge: CurrentChallenge, message: telebot.types.Message
    ) -> CheckedResult:
        current_result = self._result_storage.get_last_result(user=user, challenge=current_challenge.data)
        expectation = current_challenge.info.get_answer(current_result.phase)
        if not self._match(answer=message.text, expectation=expectation):
            logger.info(
                "User '%s' given incorrect answer for phase %s, challenge %s",
                user.nick_name,
                current_result.phase,
                current_challenge.number,
            )
            return CheckedResult(correct=False, challenge_finished=False)

        logger.info(
            "User '%s' given CORRECT answer for phase %s, challenge %s",
            user.nick_name,
            current_result.phase,
            current_challenge.number,
        )
        current_result.finished_at = get_now()
        self._result_storage.finish_phase(result=current_result, finish_time=current_result.finished_at)
        if current_result.phase == current_challenge.data.phase_amount:
            logger.info("User '%s' reached the end of challenge '%s!'", user.nick_name, current_challenge.info.name)
            equal_results = self._result_storage.get_equal_results(current_result)
            challenge_finished = self._resolve_challenge_finish(challenge=current_challenge, results=equal_results)
            if challenge_finished:
                logger.info(
                    "Challenge #%s '%s' finished with all winners resolution!",
                    current_challenge.number,
                    current_challenge.info.name,
                )
                return CheckedResult(correct=True, challenge_finished=True, winner_results=equal_results)

        next_phase = current_result.phase + 1
        self._result_storage.prepare_next_result(result=current_result, next_phase=next_phase)
        return CheckedResult(correct=True, challenge_finished=False, next_phase=next_phase)
