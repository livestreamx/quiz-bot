import abc
import logging
from typing import Iterator, Optional, cast
from uuid import uuid4

import telebot
from quiz_bot import db
from quiz_bot.storage.context_models import ContextUser

logger = logging.getLogger(__name__)


class IUserStorage(abc.ABC):
    @abc.abstractmethod
    def get_or_create_user(self, user: telebot.types.User) -> ContextUser:
        pass

    @abc.abstractmethod
    def get_user(self, user: telebot.types.User) -> Optional[ContextUser]:
        pass

    @staticmethod
    @abc.abstractmethod
    def make_unknown_context_user(user: telebot.types.User) -> ContextUser:
        pass

    @property
    @abc.abstractmethod
    def users(self) -> Iterator[ContextUser]:
        pass


class UserStorage(IUserStorage):
    def get_user(self, user: telebot.types.User) -> Optional[ContextUser]:
        with db.create_session() as session:
            internal_user = session.query(db.User).get_by_external_id(value=user.id)
            if internal_user is None:
                return None
            return cast(ContextUser, ContextUser.from_orm(internal_user))

    def get_or_create_user(self, user: telebot.types.User) -> ContextUser:
        with db.create_session() as session:
            internal_user = session.query(db.User).get_by_external_id(value=user.id)
            if internal_user is not None:
                logger.info("User %s exists", internal_user)
                return cast(ContextUser, ContextUser.from_orm(internal_user))

            logger.info("User with external_id %s not found, try to save...", user.id)
            internal_user = db.User(
                external_id=user.id,
                chitchat_id=str(uuid4()),
                first_name=user.first_name,
                last_name=user.last_name,
                nick_name=user.username,
            )
            session.add(internal_user)
        logger.info("User %s successfully saved.", internal_user)
        context_user = self.get_user(user)
        if internal_user is not None:
            return cast(ContextUser, context_user)
        raise RuntimeError("User has not been saved into database!")

    @staticmethod
    def make_unknown_context_user(user: telebot.types.User) -> ContextUser:
        return ContextUser(id=0, external_id=user.id, chitchat_id=str(uuid4()), first_name="<unknown>")

    @property
    def users(self) -> Iterator[ContextUser]:
        with db.create_session() as session:
            user_ids = session.query(db.User).get_all_user_ids()
        for user_id in user_ids:
            with db.create_session() as session:
                db_user = session.query(db.User).get_by_internal_id(user_id)
                context_user = ContextUser.from_orm(db_user)
            yield context_user
