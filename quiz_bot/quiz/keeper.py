from datetime import timedelta
from typing import Optional, Type, Union, cast

from quiz_bot.entity import ChallengeType
from quiz_bot.entity.context_models import ContextChallenge
from quiz_bot.entity.types import AnyChallengeInfo
from quiz_bot.quiz.checkers import AnyResultChecker, RegularResultChecker, StoryResultChecker
from quiz_bot.storage import IResultStorage
from quiz_bot.utils import get_now


class EmptyChallengeKeeperError(RuntimeError):
    pass


class UnsupportedChallengeTypeError(RuntimeError):
    pass


class ChallengeKeeper:
    def __init__(self, result_storage: IResultStorage) -> None:
        self._result_storage = result_storage

        self._data: Optional[ContextChallenge] = None
        self._info: Optional[AnyChallengeInfo] = None
        self._checker: Optional[AnyResultChecker] = None

    def set(self, info: AnyChallengeInfo, data: ContextChallenge) -> None:
        self._data = data
        self._info = info

    @property
    def has_data(self) -> bool:
        return all((self._info is not None, self._data is not None))

    def _ensure_existence(self) -> None:
        if not self.has_data:
            raise EmptyChallengeKeeperError("Has not got and data in ChallengeKeeper!")

    @property
    def info(self) -> AnyChallengeInfo:
        self._ensure_existence()
        return cast(AnyChallengeInfo, self._info)

    @property
    def data(self) -> ContextChallenge:
        self._ensure_existence()
        return cast(ContextChallenge, self._data)

    @property
    def number(self) -> int:
        return cast(int, self.data.id)

    @property
    def finish_after(self) -> timedelta:
        return cast(timedelta, self.data.created_at + self.info.duration - get_now())

    @property
    def finished(self) -> bool:
        return self.data.finished_at is not None

    @property
    def out_of_date(self) -> bool:
        return not self.finished and self.finish_after.total_seconds() < 0

    def _get_checker(self) -> Union[Type[RegularResultChecker], Type[StoryResultChecker]]:
        if self.info.type is ChallengeType.REGULAR:
            return RegularResultChecker
        if self.info.type is ChallengeType.STORY:
            return StoryResultChecker
        raise UnsupportedChallengeTypeError(f"Not supported challenge type: '{self.info.type}'!")

    @property
    def checker(self) -> AnyResultChecker:
        checker_cls = self._get_checker()
        if not isinstance(self._checker, checker_cls):
            self._checker = checker_cls(result_storage=self._result_storage)
        if self._checker is None:
            raise RuntimeError("Should not be there, mr mypy")
        return self._checker
