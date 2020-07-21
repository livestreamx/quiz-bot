import logging
import socket
from typing import Optional

from pydantic import BaseSettings, validator
from sqlalchemy.engine import Engine, engine_from_config
from sqlalchemy.engine.url import URL as SAURL
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.pool import SingletonThreadPool
from yarl import URL


class LoggingSettings(BaseSettings):
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


class DialogSettings(BaseSettings):
    empty_message: str = "Ответа нет " + r'¯\_(ツ)_/¯'
    greetings: str = (
        "Привет! Я T-Quiz Bot. @livestream_x создал меня для того, чтобы я выполнял функцию ведущего для проведения "
        "викторин. Чтобы начать свой путь к вершине победы, отправь команду '/start'"
    )
    unknown_warning: str = "Чтобы начать викторину, отправь команду '/start'"

    start_info: str = "Скоро здесь появится информация о викторине и условия определения победителей..."


class DataBaseSettings(BaseSettings):
    url: SAURL = 'postgresql://postgres:postgres@localhost/app'
    pool_recycle: int = 500
    pool_size: int = 6
    echo: bool = False
    application_name: str = socket.gethostname()
    connection_timeout: int = 5

    @validator('url', pre=True, always=True)
    def validate_url(cls, v: str) -> SAURL:
        try:
            return make_url(v)
        except ArgumentError as e:
            raise ValueError from e

    class Config:
        env_prefix = 'DB_'

    def setup_db(self) -> Engine:
        from db.base import metadata

        engine = engine_from_config(
            {
                'url': self.url,
                "pool_recycle": self.pool_recycle,
                "pool_pre_ping": True,
                "pool_size": self.pool_size,
                "poolclass": SingletonThreadPool,
                "connect_args": {'connect_timeout': self.connection_timeout, 'application_name': self.application_name},
            },
            prefix="",
        )
        metadata.bind = engine
        return engine  # noqa: R504
