import abc
import logging
from typing import List

from quiz_bot.manager.checkers.abstract import IResultChecker
from quiz_bot.manager.checkers.models import WinnerResult
from quiz_bot.settings import ChallengeSettings
from quiz_bot.storage import ContextChallenge, IResultStorage

logger = logging.getLogger(__name__)


class BaseResultChecker(IResultChecker, abc.ABC):
    def __init__(self, result_storage: IResultStorage, challenge_settings: ChallengeSettings):
        self._result_storage = result_storage
        self._challenge_settings = challenge_settings

    def get_winners(self, challenge: ContextChallenge) -> List[WinnerResult]:
        finished_results = self._result_storage.get_finished_results(challenge)
        winner_list: List[WinnerResult] = []
        position = 0
        for result in finished_results:
            position += 1
            winner_list.append(WinnerResult(user=result.user, position=position, finished_at=result.finished_at))
        return winner_list