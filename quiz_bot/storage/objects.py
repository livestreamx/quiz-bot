from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, List, cast

from pydantic import BaseModel, validator
from quiz_bot.models import ChallengeInfo
from quiz_bot.storage.context_models import ContextChallenge
from quiz_bot.utils import get_now


@dataclass(frozen=True)
class ExtendedChallenge:
    info: ChallengeInfo
    data: ContextChallenge
    number: int

    @property
    def finish_after(self) -> timedelta:
        return cast(timedelta, self.data.created_at + self.info.duration - (self.data.created_at + get_now()))


class AnswerResult(BaseModel):
    correct: bool = False
    replies: List[str] = []

    @validator('replies')
    def validate_replies(cls, v: List[str], values: Dict[str, Any]) -> List[str]:
        if values.get('correct') is True and not v:
            raise ValueError("Correct answer should contain at least one reply!")
        return v

    @property
    def split_replies(self) -> bool:
        return self.correct
