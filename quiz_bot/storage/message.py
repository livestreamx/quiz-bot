import abc
import logging
from typing import List, Sequence

from quiz_bot import db
from quiz_bot.entity import ContextMessage, MessageCloudSettings

logger = logging.getLogger(__name__)


class IMessageStorage(abc.ABC):
    @abc.abstractmethod
    def save(self, text: str) -> None:
        pass

    @abc.abstractmethod
    def save_all(self, texts: Sequence[str]) -> None:
        pass

    @property
    @abc.abstractmethod
    def messages(self) -> Sequence[ContextMessage]:
        pass


class MessageStorage(IMessageStorage):
    def __init__(self, settings: MessageCloudSettings) -> None:
        self._settings = settings

    def save(self, text: str) -> None:
        with db.create_session() as session:
            session.add(db.Message(text))

    def save_all(self, texts: Sequence[str]) -> None:
        with db.create_session() as session:
            for text in texts:
                session.add(db.Message(text))

    @property
    def messages(self) -> Sequence[ContextMessage]:
        with db.create_session() as session:
            message_ids = session.query(db.Message).get_message_ids(limit=self._settings.select_limit)
            messages: List[ContextMessage] = []
            if message_ids:
                for message_id in message_ids:
                    db_message = session.query(db.Message).get(message_id)
                    messages.append(ContextMessage.from_orm(db_message))
            else:
                logger.warning("No one message was found in database!")
        return messages
