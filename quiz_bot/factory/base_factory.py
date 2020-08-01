from functools import cached_property

from quiz_bot.clients import RemoteBotClient
from quiz_bot.entity import ChallengeSettings, RemoteClientSettings
from quiz_bot.manager import ChallengeMaster, ClassicResultChecker
from quiz_bot.manager.checkers import IResultChecker
from quiz_bot.storage import (
    ChallengeStorage,
    IChallengeStorage,
    IResultStorage,
    IUserStorage,
    ResultStorage,
    UserStorage,
)


class BaseQuizFactory:
    def __init__(self, challenge_settings: ChallengeSettings) -> None:
        self._challenge_settings = challenge_settings

    @cached_property
    def _remote_bot_client(self) -> RemoteBotClient:
        return RemoteBotClient(RemoteClientSettings())

    @cached_property
    def _user_storage(self) -> IUserStorage:
        return UserStorage()

    @cached_property
    def _challenge_storage(self) -> IChallengeStorage:
        return ChallengeStorage()

    @cached_property
    def _result_storage(self) -> IResultStorage:
        return ResultStorage()

    @cached_property
    def _result_checker(self) -> IResultChecker:
        return ClassicResultChecker(result_storage=self._result_storage, challenge_settings=self._challenge_settings)

    @cached_property
    def _challenge_master(self) -> ChallengeMaster:
        return ChallengeMaster(
            challenge_storage=self._challenge_storage,
            settings=self._challenge_settings,
            result_checker=self._result_checker,
        )
