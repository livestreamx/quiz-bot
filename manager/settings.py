import logging
from typing import Optional

from pydantic import BaseSettings, validator
from yarl import URL


class ApplicationSettings(BaseSettings):
    log_level: str = logging.getLevelName(logging.INFO)

    class Config:
        env_prefix = 'APP_'

    def setup_logging(self) -> None:
        logging.basicConfig(level=self.log_level)


class ChitchatClientSettings(BaseSettings):
    url: URL
    read_timeout: int = 10

    @validator('url', pre=True)
    def make_url(cls, v: Optional[str]) -> URL:
        if isinstance(v, str):
            return URL(v)
        raise ValueError

    class Config:
        env_prefix = 'CHITCHAT_'


class RemoteClientSettings(BaseSettings):
    api_key: str

    class Config:
        env_prefix = 'REMOTE_'
