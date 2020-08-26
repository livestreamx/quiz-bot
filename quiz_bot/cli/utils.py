import io
from typing import Optional, Type

from pydantic import BaseSettings


def get_settings(file: Optional[io.StringIO], settings_type: Type[BaseSettings]) -> BaseSettings:
    if file is not None:
        return settings_type.parse_raw(file.read())
    return settings_type()
