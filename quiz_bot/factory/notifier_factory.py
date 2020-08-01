from functools import cached_property

from quiz_bot.factory.base_factory import BaseQuizFactory
from quiz_bot.manager import QuizNotifier


class NotifierFactory(BaseQuizFactory):
    @cached_property
    def notifier(self) -> QuizNotifier:
        return QuizNotifier(
            user_storage=self._user_storage,
            remote_client=self._remote_bot_client,
            challenge_master=self._challenge_master,
        )
