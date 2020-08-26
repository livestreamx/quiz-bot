from quiz_bot.entity.settings import DataBaseSettings, LoggingSettings


def set_basic_settings() -> None:
    LoggingSettings().setup_logging()
    DataBaseSettings().setup_db()
