import sqlalchemy as sa
import sqlalchemy.orm as so
from db.base import Base, PrimaryKeyMixin
from db.challenge import Challenge
from db.user import User


class Result(PrimaryKeyMixin, Base):
    __tablename__ = 'results'  # type: ignore

    user_id = sa.Column(sa.Integer, sa.ForeignKey(User.id), nullable=False)
    challenge_id = sa.Column(sa.Integer, sa.ForeignKey(Challenge.id), nullable=False)
    phase = sa.Column(sa.Integer, nullable=False)
    finished_at = sa.Column(sa.DateTime(timezone=True))

    user = so.relationship(User, backref=so.backref("winner", cascade="all, delete-orphan"))
    challenge = so.relationship(Challenge, backref=so.backref("result", cascade="all, delete-orphan"))

    def __init__(self, user_id: int, challenge_id: int, phase: int) -> None:
        self.user_id = user_id
        self.challenge_id = challenge_id
        self.phase = phase
