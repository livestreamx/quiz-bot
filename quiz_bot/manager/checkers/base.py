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
        pass
