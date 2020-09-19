from datetime import timedelta
from typing import Optional, Type, Union, cast

from quiz_bot.entity import ChallengeType, SymbolReplacementSettings
from quiz_bot.entity.context_models import ContextChallenge
from quiz_bot.entity.types import AnyChallengeInfo
from quiz_bot.quiz.checkers import AnyResultChecker, RegularResultChecker, StoryResultChecker
from quiz_bot.storage import IResultStorage


class EmptyChallengeKeeperError(RuntimeError):
    pass


class UnsupportedChallengeTypeError(RuntimeError):
    pass


class ChallengeKeeper:
    def __init__(self, result_storage: IResultStorage, symbol_settings: SymbolReplacementSettings) -> None:
        self._result_storage = result_storage
        self._symbol_settings = symbol_settings

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
        return self.data.finish_after

    @property
    def finished(self) -> bool:
        return self.data.finished

    @property
    def out_of_date(self) -> bool:
        return self.data.out_of_date

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
            self._checker = checker_cls(result_storage=self._result_storage, symbol_settings=self._symbol_settings)
        if self._checker is None:
            raise RuntimeError("Should not be there, mr mypy")
        return self._checker
