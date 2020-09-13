from functools import lru_cache
from pathlib import Path

from pydantic import BaseSettings


class ApplicationPathSettings(BaseSettings):
    root_dir: Path = Path(__file__).parent.parent


@lru_cache(maxsize=None)
def get_path_settings() -> ApplicationPathSettings:
    return ApplicationPathSettings()
