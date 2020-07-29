import enum
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Dict, List

from pydantic import BaseModel, conint, root_validator, validator
from quiz_bot.storage.context_models import ContextChallenge


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

    @cached_property
    def split_replies(self) -> bool:
        return self.correct
