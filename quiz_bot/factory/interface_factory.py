from functools import cached_property

from quiz_bot.factory.manager_factory import QuizManagerFactory
from quiz_bot.quiz import QuizInterface


class QuizInterfaceFactory(QuizManagerFactory):
    @cached_property
    def interface(self) -> QuizInterface:
        return QuizInterface(client=self._remote_bot_client, manager=self.manager,)
