from functools import cached_property

from quiz_bot.clients import ChitchatClient
from quiz_bot.entity import ChallengeSettings, ChitchatSettings, InfoSettings
from quiz_bot.factory.base_factory import BaseQuizFactory
from quiz_bot.quiz import QuizInterface, QuizManager, UserMarkupMaker


class QuizInterfaceFactory(BaseQuizFactory):
    def __init__(self, challenge_settings: ChallengeSettings, chitchat_settings: ChitchatSettings) -> None:
        super().__init__(challenge_settings)
        self._chitchat_settings = chitchat_settings

    @cached_property
    def _info_settings(self) -> InfoSettings:
        return InfoSettings()

    @cached_property
    def _chitchat_client(self) -> ChitchatClient:
        return ChitchatClient(self._chitchat_settings)

    @cached_property
    def _interface_maker(self) -> UserMarkupMaker:
        return UserMarkupMaker()

    @cached_property
    def _manager(self) -> QuizManager:
        return QuizManager(
            user_storage=self._user_storage,
            chitchat_client=self._chitchat_client,
            info_settings=self._info_settings,
            markup_maker=self._interface_maker,
            challenge_master=self._challenge_master,
        )

    @cached_property
    def interface(self) -> QuizInterface:
        return QuizInterface(client=self._remote_bot_client, manager=self._manager,)
