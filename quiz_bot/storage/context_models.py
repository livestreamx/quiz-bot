from pydantic_sqlalchemy import sqlalchemy_to_pydantic
from quiz_bot import db


class ContextUser(sqlalchemy_to_pydantic(db.User)):  # type: ignore
    @property
    def full_name(self) -> str:
        name = self.first_name or ''
        if self.last_name:
            name += f' {self.last_name}'
        if self.nick_name:
            name += f' @{self.nick_name}'
        return name


class ContextChallenge(sqlalchemy_to_pydantic(db.Challenge)):  # type: ignore
    pass


class ContextResult(sqlalchemy_to_pydantic(db.Result)):  # type: ignore
    user: ContextUser
    challenge: ContextChallenge
