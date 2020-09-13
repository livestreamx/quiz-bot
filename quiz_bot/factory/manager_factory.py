from functools import cached_property

from quiz_bot.clients import RemoteBotClient, ShoutboxClient
from quiz_bot.entity import ChallengeSettings, InfoSettings, RemoteClientSettings, ShoutboxSettings
from quiz_bot.quiz import ChallengeKeeper, ChallengeMaster, QuizManager, QuizNotifier, Registrar, UserMarkupMaker
from quiz_bot.storage import (
    AttemptsStorage,
    ChallengeStorage,
    IAttemptsStorage,
    IChallengeStorage,
    IResultStorage,
    IUserStorage,
    ParticipantStorage,
    ResultStorage,
    UserStorage,
)


class QuizManagerFactory:
    def __init__(self, challenge_settings: ChallengeSettings, shoutbox_settings: ShoutboxSettings) -> None:
        self._challenge_settings = challenge_settings
        self._shoutbox_settings = shoutbox_settings
        self._remote_bot_client = RemoteBotClient(RemoteClientSettings())

    @cached_property
    def _info_settings(self) -> InfoSettings:
        return InfoSettings()

    @cached_property
    def _shoutbox_client(self) -> ShoutboxClient:
        return ShoutboxClient(self._shoutbox_settings)

    @cached_property
    def _user_storage(self) -> IUserStorage:
        return UserStorage()

    @cached_property
    def _attempts_storage(self) -> IAttemptsStorage:
        return AttemptsStorage(skip_notification_attempt_num=self._info_settings.skip_question_notification_number)

    @cached_property
    def _challenge_storage(self) -> IChallengeStorage:
        return ChallengeStorage()

    @cached_property
    def _result_storage(self) -> IResultStorage:
        return ResultStorage()

    @cached_property
    def _registrar(self) -> Registrar:
        return Registrar(storage=ParticipantStorage())

    @cached_property
    def _challenge_keeper(self) -> ChallengeKeeper:
        return ChallengeKeeper(result_storage=self._result_storage)

    @cached_property
    def challenge_master(self) -> ChallengeMaster:
        return ChallengeMaster(
            storage=self._challenge_storage,
            settings=self._challenge_settings,
            registrar=self._registrar,
            keeper=self._challenge_keeper,
        )

    @cached_property
    def _interface_maker(self) -> UserMarkupMaker:
        return UserMarkupMaker()

    @cached_property
    def manager(self) -> QuizManager:
        return QuizManager(
            user_storage=self._user_storage,
            attempts_storage=self._attempts_storage,
            shoutbox_client=self._shoutbox_client,
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
