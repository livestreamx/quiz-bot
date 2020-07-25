from collections import Sequence

import telebot
from quiz_bot.manager.objects import CheckedResult
from quiz_bot.settings import ChallengeSettings
from quiz_bot.storage import ContextResult, ContextUser, CurrentChallenge, IResultStorage
from quiz_bot.utils import get_now


class ResultChecker:
    def __init__(self, result_storage: IResultStorage, challenge_settings: ChallengeSettings):
        self._result_storage = result_storage
        self._challenge_settings = challenge_settings

    @staticmethod
    def _match(answer: str, expectation: str) -> bool:
        return answer.lower() == expectation.lower()  # TODO: сделать умное сравнение

    @staticmethod
    def _resolve_challenge_finish(challenge: CurrentChallenge, results: Sequence[ContextResult]) -> bool:
        return bool(len(results) == challenge.data.winner_amount)

    def check_answer(
        self, user: ContextUser, current_challenge: CurrentChallenge, message: telebot.types.Message
    ) -> CheckedResult:
        current_result = self._result_storage.get_last_result(user=user)
        expectation = current_challenge.info.answers[current_result.phase]
        if not self._match(answer=message.text, expectation=expectation):
            return CheckedResult(correct=False, challenge_finished=False)

        current_result.finished_at = get_now()
        self._result_storage.finish_phase(result=current_result, finish_time=current_result.finished_at)
        if current_result.phase == current_challenge.data.phase_amount:
            equal_results = self._result_storage.get_equal_results(current_result)
            challenge_finished = self._resolve_challenge_finish(challenge=current_challenge, results=equal_results)
            if challenge_finished:
                return CheckedResult(correct=True, challenge_finished=True, winner_results=equal_results)

        next_phase = current_result.phase + 1
        self._result_storage.prepare_next_result(result=current_result, next_phase=next_phase)
        return CheckedResult(correct=True, challenge_finished=False, next_phase=next_phase)
