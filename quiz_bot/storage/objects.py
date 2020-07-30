from dataclasses import dataclass
from typing import Any, Dict, List

from pydantic import BaseModel, validator
from quiz_bot.models import ChallengeInfo
from quiz_bot.storage.context_models import ContextChallenge


@dataclass(frozen=True)
class CurrentChallenge:
    info: ChallengeInfo
    data: ContextChallenge
    number: int


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
