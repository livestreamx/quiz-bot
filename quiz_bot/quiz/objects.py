import enum


class ApiCommand(str, enum.Enum):
    START = 'start'
    HELP = 'help'
    STATUS = 'status'

    @property
    def as_url(self) -> str:
        return f"/{self.value}"


class ContentType(str, enum.Enum):
    TEXT = 'text'
