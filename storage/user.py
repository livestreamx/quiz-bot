import abc
import logging
from typing import Optional, Dict
from uuid import uuid4

import telebot
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class User(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    nick_name: Optional[str] = Field(None, alias='username')

    external_id: int = Field(..., alias='id')
    internal_id: Optional[int]  # reserved for Database
    chitchat_id: str = str(uuid4())

    @property
    def full_name(self) -> str:
        name = self.first_name or ''
        if self.last_name:
            name += f' {self.last_name}'
        if self.nick_name:
            name += f' @{self.nick_name}'
        return name


class IUserStorage(abc.ABC):
    @abc.abstractmethod
    def get_or_create_user(self, user: telebot.types.User) -> User:
        pass

    @abc.abstractmethod
    def get_user_by_external_id(self, external_id: int) -> Optional[User]:
        pass


class UserStorage(IUserStorage):
    def __init__(self) -> None:
        self._users: Dict[int, User] = {}

    def get_or_create_user(self, user: telebot.types.User) -> User:
        internal_user = self._users.get(user.id)
        if internal_user is not None:
            logger.info("User %s already exists", internal_user)
            return internal_user

        logger.info("User with external_id %s not found, try to save...", user.id)
        internal_user = User.parse_obj(user.to_dict())
        self._users[internal_user.external_id] = internal_user
        logger.info("User %s successfully saved", internal_user)
        return internal_user

    def get_user_by_external_id(self, external_id: int) -> Optional[User]:
        return self._users.get(external_id)
