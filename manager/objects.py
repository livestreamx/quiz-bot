import enum
from typing import Any, Dict, List

from pydantic import BaseModel, conint, root_validator


class ApiCommand(str, enum.Enum):
    START = 'start'
    HELP = 'help'

    @property
    def as_url(self) -> str:
        return f"/{self.value}"


class ContentType(str, enum.Enum):
    TEXT = 'text'


class ChallengeModel(BaseModel):
    name: str
    description: str
    questions: List[str]
    answers: List[str]
    max_winners: conint(ge=1) = 1

    @root_validator
    def validate_questions_and_answers(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        questions = values.get('questions')
        answers = values.get('answers')
        if questions is None or answers is None or not isinstance(questions, list) or not isinstance(answers, list):
            raise ValueError("Questions and answers should be set as list!")
        if len(questions) != len(answers):
            raise ValueError("Length of questions (%s) is not equal to length of answers (%s)!", questions, answers)
        return values
