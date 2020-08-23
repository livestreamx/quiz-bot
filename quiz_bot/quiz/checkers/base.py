import abc
import logging

from quiz_bot.entity import ContextParticipant, ContextResult
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
