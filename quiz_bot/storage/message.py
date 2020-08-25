import abc
import logging
from typing import Iterator

import telebot
from quiz_bot import db
from quiz_bot.entity import ContextMessage, ContextUser

logger = logging.getLogger(__name__)


class IMessageStorage(abc.ABC):
    @abc.abstractmethod
    def create(self, user: ContextUser, message: telebot.types.Message) -> None:
        pass

    @property
    @abc.abstractmethod
    def messages(self) -> Iterator[ContextMessage]:
        pass


class MessageStorage(IMessageStorage):
    def create(self, user: ContextUser, message: telebot.types.Message) -> None:
        if message.text:
            with db.create_session() as session:
                session.add(db.Message(user_id=user.id, text=message.text))

    @property
    def messages(self) -> Iterator[ContextMessage]:
        with db.create_session() as session:
            message_ids = session.query(db.Message).get_all_message_ids()
        if not message_ids:
            logger.warning("No one message was found in database!")
            return
        for message_id in message_ids:
            with db.create_session() as session:
                db_message = session.query(db.User).get(message_id)
                context_message = ContextMessage.from_orm(db_message)
            yield context_message
