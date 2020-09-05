from functools import cached_property

from quiz_bot.clients import RemoteBotClient
from quiz_bot.entity import RemoteClientSettings
from quiz_bot.quiz.interfaces import ChatInterface
from quiz_bot.storage import IUserStorage, UserStorage


class ChatFactory:
    def __init__(self, target_user: str) -> None:
        self._target_user = target_user

    @cached_property
    def _remote_bot_client(self) -> RemoteBotClient:
        return RemoteBotClient(RemoteClientSettings())

    @cached_property
    def _user_storage(self) -> IUserStorage:
        return UserStorage()

    @cached_property
    def interface(self) -> ChatInterface:
        return ChatInterface(
            client=self._remote_bot_client, user_storage=self._user_storage, target_user=self._target_user
        )
