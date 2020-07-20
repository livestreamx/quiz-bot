from datetime import datetime

from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declared_attr, as_declarative
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, scoped_session

metadata = MetaData()


@as_declarative(metadata=metadata)
class Base:
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()  # type: ignore


class PrimaryKeyMixin:
    id: int = sa.Column(sa.Integer, primary_key=True)
    created_at: datetime = sa.Column(sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now())


Session = sessionmaker()
current_session = scoped_session(Session)
