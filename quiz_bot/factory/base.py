from functools import cached_property

from quiz_bot.clients import RemoteBotClient
from quiz_bot.entity import RemoteClientSettings
from quiz_bot.storage import (
    ChallengeStorage,
    IChallengeStorage,
    IResultStorage,
    IUserStorage,
    ResultStorage,
    UserStorage,
)


class BaseQuizFactory:
    @cached_property
    def _user_storage(self) -> IUserStorage:
        return UserStorage()

    @cached_property
    def _remote_bot_client(self) -> RemoteBotClient:
        return RemoteBotClient(RemoteClientSettings())

    @cached_property
    def _challenge_storage(self) -> IChallengeStorage:
        return ChallengeStorage()

    @cached_property
    def _result_storage(self) -> IResultStorage:
        return ResultStorage()
