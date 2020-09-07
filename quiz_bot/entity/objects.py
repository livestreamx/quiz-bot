import enum
from datetime import datetime
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import BaseModel, conint, root_validator, validator
from pydantic.datetime_parse import timedelta
from quiz_bot.entity.context_models import ContextUser
from quiz_bot.entity.errors import PictureNotExistError
from quiz_bot.path import get_path_settings


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
    REGULAR = "classic"
    STORY = "story"


class PictureLocation(str, enum.Enum):
    ABOVE = "above"
    BELOW = "below"


class PictureModel(BaseModel):
    file: Path
    location: PictureLocation


class BaseChallengeInfo(BaseModel):
    name: str
    description: str
    picture: Optional[PictureModel]

    max_winners: conint(ge=1) = 1  # type: ignore
    duration: timedelta = timedelta(days=1)

    type: ChallengeType

    @validator('picture')
    def validate_picture(cls, v: Optional[PictureModel]) -> Optional[PictureModel]:
        if isinstance(v, PictureModel):
            path = get_path_settings().root_dir / v.file
            if not path.exists():
                raise PictureNotExistError(f"Specified picture '{v}' does not exist with path '{path}'!")
            v.file = path
        return v


class RegularChallengeInfo(BaseChallengeInfo):
    type: ChallengeType = ChallengeType.REGULAR

    questions: List[str]
    answers: List[Union[str, Set[str]]]

    @root_validator
    def validate_questions_and_answers(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        questions = values.get('questions')
        answers = values.get('answers')
        if questions is None or answers is None or not isinstance(questions, list) or not isinstance(answers, list):
            raise ValueError("Questions and answers should be set as list!")
        if len(questions) != len(answers):
            raise ValueError("Length of questions (%s) is not equal to length of answers (%s)!", questions, answers)
        return values

    def get_question(self, number: int) -> str:
        return self.questions[number - 1]

    def get_answer_variants(self, number: int) -> Set[str]:
        answer = self.answers[number - 1]
        if isinstance(answer, str):
            return {answer}
        return answer

    @property
    def phase_amount(self) -> int:
        return len(self.questions)


class StoryStep(str, enum.Enum):
    GIVEN = "Дано"
    WHEN = "Когда"
    THEN = "Тогда"


class StoryPreposition(str, enum.Enum):
    AND = "И"
    BUT = "Но"


_PREPOSITION_PARSER_DELIMITER = "|"


class StoryItem(BaseModel):
    step: StoryStep
    prepositions: Optional[List[StoryPreposition]]
    construction: str
    text: str

    @root_validator
    def validate_step_with_preposition(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        step = values.get('step')
        if isinstance(step, str):
            if _PREPOSITION_PARSER_DELIMITER in step:
                splitted = step.split(_PREPOSITION_PARSER_DELIMITER)
                values["prepositions"] = list(
                    filter(lambda x: x in (s.value for s in list(StoryPreposition)), splitted)
                )
                values["step"] = list(filter(lambda x: x in (s.value for s in list(StoryStep)), splitted))
            return values
        raise ValueError("Step should be specififed!")


class StoryChallengeInfo(BaseChallengeInfo):
    type: ChallengeType = ChallengeType.STORY
    items: List[StoryItem]

    @property
    def phase_amount(self) -> int:
        return 1


class AnswerEvaluation(BaseModel):
    status: EvaluationStatus
    replies: List[str] = []
    quiz_state: QuizState = QuizState.IN_PROGRESS
    picture: Optional[PictureModel]

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
