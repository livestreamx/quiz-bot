import enum
from dataclasses import dataclass
from datetime import datetime
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union, cast

from pydantic import BaseModel, conint, root_validator, validator
from pydantic.datetime_parse import timedelta
from quiz_bot.entity.context_models import ContextChallenge, ContextUser
from quiz_bot.entity.errors import PictureNotExistError
from quiz_bot.path import get_path_settings
from quiz_bot.utils import get_now


class QuizState(str, enum.Enum):
    NEW = "new"  # Quiz has not been started yet
    IN_PROGRESS = "in_progress"  # Quiz is having active challenge at the moment
    WAIT_NEXT = "wait_next"  # Quiz has finished and not finished challenges, waiting for starting next challenge
    FINISHED = "finished"  # Quiz has been finished

    @cached_property
    def prepared(self) -> bool:
        return self in [QuizState.NEW, QuizState.WAIT_NEXT]

    @cached_property
    def delivered(self) -> bool:  # Quiz has been started and reached some challenge's end. Maybe, quiz finished also.
        return self in [QuizState.WAIT_NEXT, QuizState.FINISHED]


class EvaluationStatus(str, enum.Enum):
    CORRECT = "correct"  # Evaluation has been checked and it is correct
    INCORRECT = "incorrect"  # Evaluation has been checked and it is incorrect
    NOT_CHECKED = "not_checked"  # Evaluation has not been checked due to circumstances


class ChallengeType(str, enum.Enum):
    CLASSIC = "classic"
    SCRIPT = "script"


class ChallengeInfo(BaseModel):
    name: str
    description: str
    picture: Optional[Path]
    questions: List[str]
    answers: List[Union[str, Set[str]]]
    max_winners: conint(ge=1) = 1  # type: ignore

    type: ChallengeType = ChallengeType.CLASSIC
    duration: timedelta = timedelta(days=1)

    @root_validator
    def validate_questions_and_answers(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        questions = values.get('questions')
        answers = values.get('answers')
        if questions is None or answers is None or not isinstance(questions, list) or not isinstance(answers, list):
            raise ValueError("Questions and answers should be set as list!")
        if len(questions) != len(answers):
            raise ValueError("Length of questions (%s) is not equal to length of answers (%s)!", questions, answers)
        return values

    @validator('picture', pre=True)
    def validate_picture(cls, v: Optional[str]) -> Optional[Path]:
        if isinstance(v, str):
            path = get_path_settings().root_dir / v
            if path.exists():
                return path
            raise PictureNotExistError(f"Specified picture '{v}' does not exist with path '{path}'!")
        return None

    def get_question(self, number: int) -> str:
        return self.questions[number - 1]

    def get_answer_variants(self, number: int) -> Set[str]:
        answer = self.answers[number - 1]
        if isinstance(answer, str):
            return {answer}
        return answer


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


class AnswerEvaluation(BaseModel):
    status: EvaluationStatus
    replies: List[str] = []
    quiz_state: QuizState = QuizState.IN_PROGRESS

    @validator('replies')
    def validate_replies(cls, v: List[str], values: Dict[str, Any]) -> List[str]:
        if values.get('status') is EvaluationStatus.CORRECT and not v:
            raise ValueError("Correct answer should contain at least one reply!")
        return v


class CheckedResult(BaseModel):
    correct: bool
    next_phase: Optional[int]


class WinnerResult(BaseModel):
    user: ContextUser
    position: int
    scores: int
    finished_at: datetime
