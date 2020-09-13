import enum


class ApiCommand(str, enum.Enum):
    START = 'start'
    HELP = 'help'
    STATUS = 'status'
    SKIP = 'skip'

    @property
    def as_url(self) -> str:
        return f"/{self.value}"


class SkipApprovalCommand(str, enum.Enum):
    YES = f"{ApiCommand.SKIP.as_url}/yes"
    NO = f"{ApiCommand.SKIP.as_url}/no"


class ContentType(str, enum.Enum):
    TEXT = 'text'


ChatEmptyReply = "Skip"
