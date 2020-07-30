from datetime import datetime
from typing import Optional

from pydantic.main import BaseModel
from quiz_bot.storage import ContextUser


class CheckedResult(BaseModel):
    correct: bool
    challenge_finished: bool
    next_phase: Optional[int]

    @property
    def finished_for_user(self) -> bool:
        return self.correct is True and self.next_phase is None


class WinnerResult(BaseModel):
    user: ContextUser
    position: int
    finished_at: datetime

    @property
    def first(self) -> bool:
        return self.position == 1