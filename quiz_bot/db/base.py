from typing import Type

import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import as_declarative, declared_attr

metadata = MetaData()


@as_declarative(metadata=metadata)
class Base:
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()  # type: ignore


class PrimaryKeyMixin:
    id = sa.Column(sa.Integer, primary_key=True)
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now())


def _get_query_cls(mapper: Type[Base], session: so.Session) -> so.Query:
    if mapper:
        m = mapper
        if isinstance(m, tuple):
            m = mapper[0]
        if isinstance(m, so.Mapper):
            m = m.entity
        return m.__query_cls__(mapper, session)  # type: ignore
    return so.Query(mapper, session)


Session = so.sessionmaker(query_cls=_get_query_cls)
current_session = so.scoped_session(Session)
