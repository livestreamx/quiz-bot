from pydantic import BaseModel


class ChitChatRequest(BaseModel):
    text: str
    user_id: str
    force_full_mode: bool = True


class ChitChatResponse(BaseModel):
    text: str
