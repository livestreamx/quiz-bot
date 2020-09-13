import abc
import logging

from quiz_bot.entity import CheckedResult, ContextChallenge, ContextParticipant, ContextResult, TChallengeInfo
from quiz_bot.quiz.checkers.abstract_checker import IResultChecker
from quiz_bot.storage import IResultStorage
from quiz_bot.utils import get_now

logger = logging.getLogger(__name__)


class BaseResultChecker(IResultChecker[TChallengeInfo], abc.ABC):
    def __init__(self, result_storage: IResultStorage):
        self._result_storage = result_storage

    def create_initial_phase(self, participant: ContextParticipant) -> ContextResult:
        return self._result_storage.create_result(participant_id=participant.id, phase=1)

    def _set_phase_finished(self, result: ContextResult) -> None:
        result.finished_at = get_now()
        self._result_storage.finish_phase(result=result, finish_time=result.finished_at)

    def _next_result(
        self, participant: ContextParticipant, data: ContextChallenge, current_result: ContextResult
    ) -> CheckedResult:
        self._set_phase_finished(current_result)
        if current_result.phase == data.phase_amount:
            logger.debug("CurrentResult phase is equal to ContextChallenge phase_amount, so next_phase is None")
            return CheckedResult(correct=True)

        next_phase = current_result.phase + 1
        logger.debug(
            "Next phase for user '%s' in challenge ID %s is %s", participant.user.nick_name, data.id, next_phase
        )
        self._result_storage.create_result(participant_id=participant.id, phase=next_phase)
        return CheckedResult(correct=True, next_phase=next_phase)

    def skip_question(self, participant: ContextParticipant, data: ContextChallenge) -> CheckedResult:
        current_result = self._result_storage.get_last_result(participant_id=participant.id)
        logger.info(
            "User '%s' SKIP answer for phase %s, challenge %s",
            participant.user.nick_name,
            current_result.phase,
            data.id,
        )
        return self._next_result(participant=participant, data=data, current_result=current_result,)
