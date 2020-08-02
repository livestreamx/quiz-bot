import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from pydantic import BaseModel, conint, root_validator, validator
from pydantic.datetime_parse import timedelta
from quiz_bot.entity.context_models import ContextChallenge, ContextUser
from quiz_bot.utils import get_now


class ChallengeType(str, enum.Enum):
    CLASSIC = "classic"
    SCRIPT = "script"


class ChallengeInfo(BaseModel):
    name: str
    description: str
    questions: List[str]
    answers: List[str]
    max_winners: conint(ge=1) = 1  # type: ignore

    type: ChallengeType = ChallengeType.CLASSIC
    duration: timedelta = timedelta(days=1)

    def get_question(self, number: int) -> str:
        return self.questions[number - 1]

    def get_answer(self, number: int) -> str:
        return self.answers[number - 1]

    @root_validator
    def validate_questions_and_answers(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        questions = values.get('questions')
        answers = values.get('answers')
        if questions is None or answers is None or not isinstance(questions, list) or not isinstance(answers, list):
            raise ValueError("Questions and answers should be set as list!")
        if len(questions) != len(answers):
            raise ValueError("Length of questions (%s) is not equal to length of answers (%s)!", questions, answers)
        return values


@dataclass(frozen=True)
class ExtendedChallenge:
    info: ChallengeInfo
    data: ContextChallenge
    number: int

    @property
    def finish_after(self) -> timedelta:
        return cast(timedelta, self.data.created_at + self.info.duration - get_now())

    @property
    def finished(self) -> bool:
        return self.data.finished_at is not None

    @property
    def out_of_date(self) -> bool:
        return not self.finished and self.finish_after.total_seconds() < 0


class ChallengeEvaluation(BaseModel):
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


class CheckedResult(BaseModel):
    correct: bool
    finish_condition_reached: bool
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
