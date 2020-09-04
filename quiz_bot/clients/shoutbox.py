import logging
import re
from functools import cached_property

import requests
import tenacity
from pydantic import BaseModel
from quiz_bot.entity import ShoutboxSettings

logger = logging.getLogger(__name__)


class ShoutboxPrewrittenDetectedError(RuntimeError):
    pass


class ShoutboxRequest(BaseModel):
    text: str
    user_id: str
    force_full_mode: bool = True


class ShoutboxResponse(BaseModel):
    text: str


class ShoutboxClient:
    def __init__(self, settings: ShoutboxSettings):
        self._settings = settings
        self._prewritten = re.compile(rf"({')+|('.join(settings.filter_phrases)})+", flags=re.I)

    def _detect_prewritten(self, text: str) -> bool:
        return bool(self._prewritten.search(text))

    @cached_property
    def enabled(self) -> bool:
        return self._settings.url is not None

    @tenacity.retry(
        reraise=True,
        retry=tenacity.retry_if_exception_type(requests.RequestException),
        stop=tenacity.stop_after_attempt(3),
        before_sleep=tenacity.before_sleep_log(logger, logger.level),
        after=tenacity.after_log(logger, logger.level),
    )
    def make_request(self, data: ShoutboxRequest) -> ShoutboxResponse:
        if self._settings.url is None:
            raise RuntimeError("Shoutbox is disabled, so should not be here!")
        response = requests.post(
            self._settings.url.human_repr(), json=data.dict(), timeout=self._settings.read_timeout,
        )
        response.raise_for_status()
        model = ShoutboxResponse.parse_obj(response.json())

        if self._detect_prewritten(model.text):
            raise ShoutboxPrewrittenDetectedError(f"Detected shoutbox prewritten: '{model.text}'",)
        return model
