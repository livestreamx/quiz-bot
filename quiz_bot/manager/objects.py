import enum
from dataclasses import dataclass


class ApiCommand(str, enum.Enum):
    START = 'start'
    HELP = 'help'

    @property
    def as_url(self) -> str:
        return f"/{self.value}"


class ContentType(str, enum.Enum):
    TEXT = 'text'


@dataclass(frozen=True)
class CheckedResult:
    correct: bool
    challenge_finished: bool
