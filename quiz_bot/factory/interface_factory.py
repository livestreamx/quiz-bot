from functools import cached_property

from quiz_bot.entity import MessageCloudSettings
from quiz_bot.factory.manager_factory import QuizManagerFactory
from quiz_bot.quiz import QuizInterface
from quiz_bot.storage import IMessageStorage, MessageStorage


class QuizInterfaceFactory(QuizManagerFactory):
    @cached_property
    def _message_storage(self) -> IMessageStorage:
        return MessageStorage(MessageCloudSettings())

    @cached_property
    def interface(self) -> QuizInterface:
        return QuizInterface(
            client=self._remote_bot_client, manager=self.manager, message_storage=self._message_storage
        )
