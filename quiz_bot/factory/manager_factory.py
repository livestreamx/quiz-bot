from functools import cached_property

from quiz_bot.clients import ChitchatClient, RemoteBotClient
from quiz_bot.entity import ChallengeSettings, ChitchatSettings, InfoSettings, RemoteClientSettings
from quiz_bot.quiz import ChallengeMaster, ClassicResultChecker, QuizManager, QuizNotifier, UserMarkupMaker
from quiz_bot.quiz.checkers import IResultChecker
from quiz_bot.storage import (
    ChallengeStorage,
    IChallengeStorage,
    IResultStorage,
    IUserStorage,
    ResultStorage,
    UserStorage,
)


class QuizManagerFactory:
    def __init__(self, challenge_settings: ChallengeSettings, chitchat_settings: ChitchatSettings) -> None:
        self._challenge_settings = challenge_settings
        self._chitchat_settings = chitchat_settings

    @cached_property
    def _info_settings(self) -> InfoSettings:
        return InfoSettings()

    @cached_property
    def _remote_bot_client(self) -> RemoteBotClient:
        return RemoteBotClient(RemoteClientSettings())

    @cached_property
    def _chitchat_client(self) -> ChitchatClient:
        return ChitchatClient(self._chitchat_settings)

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
    def challenge_master(self) -> ChallengeMaster:
        return ChallengeMaster(
            storage=self._challenge_storage, settings=self._challenge_settings, result_checker=self._result_checker,
        )

    @cached_property
    def _interface_maker(self) -> UserMarkupMaker:
        return UserMarkupMaker()

    @cached_property
    def manager(self) -> QuizManager:
        return QuizManager(
            user_storage=self._user_storage,
            chitchat_client=self._chitchat_client,
            settings=self._info_settings,
            markup_maker=self._interface_maker,
            challenge_master=self.challenge_master,
        )

    @cached_property
    def notifier(self) -> QuizNotifier:
        return QuizNotifier(
            user_storage=self._user_storage,
            remote_client=self._remote_bot_client,
            settings=self._info_settings,
            markup_maker=self._interface_maker,
            challenge_master=self.challenge_master,
        )
