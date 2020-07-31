import io
from typing import Optional, Type

from pydantic import BaseSettings
from quiz_bot.entity import DataBaseSettings, LoggingSettings


def set_basic_settings() -> None:
    LoggingSettings().setup_logging()
    DataBaseSettings().setup_db()


def get_settings(file: Optional[io.StringIO], settings_type: Type[BaseSettings]) -> BaseSettings:
    if file is not None:
        return settings_type.parse_raw(file.read())
    return settings_type()
