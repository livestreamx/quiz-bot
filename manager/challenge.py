import abc
from typing import Optional

import telebot
from storage import ContextUser, ContextChallenge
from storage.challenge import IChallengeStorage
from storage.result import ResultStorage

from manager.objects import ChallengeModel
from manager.settings import ChallengeSettings


class IChallengeMaster(abc.ABC):
    @abc.abstractmethod
    def start_next_challenge(self) -> None:
        pass

    @property
    @abc.abstractmethod
    def current_challenge(self) -> Optional[ChallengeModel]:
        pass

    @abc.abstractmethod
    def resolve_challenge(self, message: telebot.types.Message) -> ChallengeModel:
        pass


class IChallengeInfo(abc.ABC):
    @property
    @abc.abstractmethod
    def start_info(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def winner_info(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def finish_info(self) -> str:
        pass


class ChallengeMaster(IChallengeMaster, IChallengeInfo):
    def __init__(
        self, challenge_storage: IChallengeStorage, result_storage: ResultStorage, settings: ChallengeSettings
    ) -> None:
        self._challenge_storage = challenge_storage
        self._result_storage = result_storage
        self._settings = settings

        self._current_challenge: Optional[ChallengeModel] = None
        self._current_challenge_number: Optional[int] = None
        self._resolve()

    def _resolve(self) -> None:
        for challenge in self._settings.challenges:
            self._challenge_storage.create_challenge(name=challenge.name)
        self._synchronize_current_challenge()

    def _resolve_current_attrs(self, challenge: Optional[ContextChallenge]) -> None:
        if challenge is None:
            self._current_challenge_number = None
            self._current_challenge = None
            return
        self._current_challenge_number = challenge.id
        self._current_challenge = self._settings.get_challenge_by_name(challenge.name)

    def _synchronize_current_challenge(self) -> None:
        self._resolve_current_attrs(challenge=self._challenge_storage.get_actual_challenge())

    def start_next_challenge(self) -> None:
        self._resolve_current_attrs(challenge=self._challenge_storage.start_next_challenge())

    @property
    def current_challenge(self) -> Optional[ChallengeModel]:
        return self._current_challenge

    def resolve_challenge(self, user: ContextUser, message: telebot.types.Message) -> ChallengeModel:
        pass

    @property
    def start_info(self) -> str:
        return self._settings.get_start_notification(
            challenge_num=self._current_challenge_number,
            challenge_name=self._current_challenge.name,
            description=self._current_challenge.description,
        )
