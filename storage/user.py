import abc
import logging
from typing import Optional, cast
from uuid import uuid4

import db
import sqlalchemy.orm as so
import telebot
from storage.models import ContextUser

logger = logging.getLogger(__name__)


class IUserStorage(abc.ABC):
    @abc.abstractmethod
    def get_or_create_user(self, user: telebot.types.User) -> ContextUser:
        pass

    @abc.abstractmethod
    def get_user(self, user: telebot.types.User) -> Optional[ContextUser]:
        pass


class UserStorage(IUserStorage):
    @staticmethod
    def _get_db_user(session: so.Session, external_id: int) -> Optional[db.User]:
        return cast(Optional[db.User], session.query(db.User).filter(db.User.external_id == external_id).one_or_none())

    def get_user(self, user: telebot.types.User) -> Optional[ContextUser]:
        with db.create_session() as session:
            internal_user = self._get_db_user(session, external_id=user.id)
            if internal_user is None:
                return None
            return cast(ContextUser, ContextUser.from_orm(internal_user))

    def get_or_create_user(self, user: telebot.types.User) -> ContextUser:
        with db.create_session() as session:
            internal_user = self._get_db_user(session, external_id=user.id)
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
        internal_user = self.get_user(user)
        if internal_user is not None:
            return internal_user
        raise RuntimeError("User has not been saved into database!")
