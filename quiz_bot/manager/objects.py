import enum
from typing import List, Optional

from pydantic.main import BaseModel
from quiz_bot.storage import ContextResult


class ApiCommand(str, enum.Enum):
    START = 'start'
    HELP = 'help'

    @property
    def as_url(self) -> str:
        return f"/{self.value}"


class ContentType(str, enum.Enum):
    TEXT = 'text'


class CheckedResult(BaseModel):
    correct: bool
    challenge_finished: bool
    next_phase: Optional[int]
    winner_results: Optional[List[ContextResult]]
