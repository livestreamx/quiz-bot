import logging

import requests
import tenacity
from pydantic import BaseModel
from quiz_bot.manager import ChitchatClientSettings

logger = logging.getLogger(__name__)


class ChitChatRequest(BaseModel):
    text: str
    user_id: str
    force_full_mode: bool = True


class ChitChatResponse(BaseModel):
    text: str


class ChitchatClient:
    def __init__(self, settings: ChitchatClientSettings):
        self._settings = settings

    @tenacity.retry(
        reraise=True,
        retry=tenacity.retry_if_exception_type(requests.RequestException),
        stop=tenacity.stop_after_attempt(3),
        before_sleep=tenacity.before_sleep_log(logger, logger.level),
        after=tenacity.after_log(logger, logger.level),
    )
    def make_request(self, data: ChitChatRequest) -> ChitChatResponse:
        response = requests.post(
            self._settings.url.human_repr(), json=data.dict(), timeout=self._settings.read_timeout,
        )
        response.raise_for_status()
        return ChitChatResponse.parse_obj(response.json())
