from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import scoped_session, sessionmaker

metadata = MetaData()


@as_declarative(metadata=metadata)
class Base:
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()  # type: ignore


class PrimaryKeyMixin:
    id = sa.Column(sa.Integer, primary_key=True)
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now())


Session = sessionmaker()
current_session = scoped_session(Session)
