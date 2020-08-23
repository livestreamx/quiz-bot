import abc
import logging

from quiz_bot.entity import CheckedResult, ContextParticipant, ContextResult, ExtendedChallenge
from quiz_bot.quiz.checkers.abstract import IResultChecker
from quiz_bot.storage import IResultStorage
from quiz_bot.utils import get_now

logger = logging.getLogger(__name__)


class BaseResultChecker(IResultChecker, abc.ABC):
    def __init__(self, result_storage: IResultStorage):
        self._result_storage = result_storage

    def create_initial_phase(self, participant: ContextParticipant) -> ContextResult:
        return self._result_storage.create_result(participant_id=participant.id, phase=1)

    def _set_phase_finished(self, result: ContextResult) -> None:
        result.finished_at = get_now()
        self._result_storage.finish_phase(result=result, finish_time=result.finished_at)

    def _next_result(
        self, participant: ContextParticipant, current_challenge: ExtendedChallenge, current_result: ContextResult
    ) -> CheckedResult:
        self._set_phase_finished(current_result)
        if current_result.phase == current_challenge.data.phase_amount:
            return CheckedResult(correct=True)

        next_phase = current_result.phase + 1
        self._result_storage.create_result(participant_id=participant.id, phase=next_phase)
        return CheckedResult(correct=True, next_phase=next_phase)

    def skip_question(self, participant: ContextParticipant, current_challenge: ExtendedChallenge) -> CheckedResult:
        current_result = self._result_storage.get_last_result(participant_id=participant.id)
        logger.info(
            "User '%s' SKIP answer for phase %s, challenge %s",
            participant.user.nick_name,
            current_result.phase,
            current_challenge.number,
        )
        return self._next_result(
            participant=participant, current_challenge=current_challenge, current_result=current_result,
        )
