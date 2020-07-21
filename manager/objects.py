import enum

from pydantic import BaseModel


class ApiCommand(str, enum.Enum):
    START = 'start'
    HELP = 'help'

    @property
    def as_url(self) -> str:
        return f"/{self.value}"


class ContentType(str, enum.Enum):
    TEXT = 'text'


class ChitChatRequest(BaseModel):
    text: str
    user_id: str
    force_full_mode: bool = True


class ChitChatResponse(BaseModel):
    text: str
