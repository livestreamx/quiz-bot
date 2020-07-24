from contextlib import contextmanager
from typing import Any, Iterator

import sqlalchemy.orm as so
from quiz_bot.db.base import Session


@contextmanager
def create_session(**kwargs: Any) -> Iterator[so.Session]:
    """Provide a transactional scope around a series of operations."""
    new_session = Session(**kwargs)
    try:
        yield new_session
        new_session.commit()
    except Exception:
        new_session.rollback()
        raise
    finally:
        new_session.close()
