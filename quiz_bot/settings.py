import logging
import socket
from datetime import datetime
from random import choice
from typing import Dict, List, Optional, Sequence

from pydantic import BaseSettings, validator
from quiz_bot.storage import ChallengeInfo
from quiz_bot.storage.errors import NotEqualChallengesAmount, UnexpectedChallengeNameError
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


class ChitchatSettings(BaseSettings):
    url: URL
    read_timeout: int = 10
    filter_phrases: List[str] = [
        "совет дня",
        "вопрос дня",
        "давай экономить",
        "деньги",
        "деньгах",
        "Олег",
        "позвать человека",
        "сделает вашу жизнь проще",
    ]

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


class InfoSettings(BaseSettings):
    empty_message: str = "Нечего сказать " + r'¯\_(ツ)_/¯'
    greetings: str = (
        "Мое имя - T-Quiz Bot. @livestream_x создал меня для того, чтобы я выполнял функцию ведущего для проведения "
        "викторин. Чтобы начать свой путь к вершине победы, нажми на кнопку старта."
    )
    unknown_info: str = "Если хочешь узнать, что я за бот такой - нажми на кнопку помощи."


class ChallengeSettings(BaseSettings):
    challenges: List[ChallengeInfo]

    start_notification: str = "Начинается испытание #{number} '{name}'. {description}"
    finish_notification: str = "Завершено испытание #{number} '{name}'."
    winner_notification: str = "Мои поздравления - вы стали победителем в испытании '{name}'!"
    progress_notification: str = "В испытании '{name}' - победитель @{nick_name} ({timestamp})."

    correct_answer_notifications: List[str] = ["Верно.", "Молодец!", "Так держать!", "И, правда, так."]
    incorrect_answer_notifications: List[str] = [
        "Неверно.",
        "И, нет, ответ неправильный.",
        "И в этот раз не получилось попасть в ответ.",
        "...в общем, не правильно 😔",
    ]
    next_answer_notification: str = "Вопрос #{number}: {question}"

    end_info: str = "Итоги викторины:\n{results}\n\nВикторина завершена, спасибо за участие!"
    results_row: str = "Испытание #{number} '{name}': "
    post_end_info: str = "Викторина завершена, спасибо за участие!"

    @property
    def random_correct_answer_notification(self) -> str:
        return choice(self.correct_answer_notifications)

    @property
    def random_incorrect_answer_notification(self) -> str:
        return choice(self.incorrect_answer_notifications)

    def get_challenge_by_name(self, name: str) -> ChallengeInfo:
        for challenge in self.challenges:
            if challenge.name != name:
                continue
            return challenge
        raise UnexpectedChallengeNameError(
            f"'{name}' not found in challenges: {[x.name for x in self.challenges]}"
            "If you want to change challenges - please, clear database and start application again."
        )

    def get_start_notification(self, challenge_num: int, challenge_name: str, description: str) -> str:
        return self.start_notification.format(number=challenge_num, name=challenge_name, description=description)

    def get_finish_notification(self, challenge_num: int, challenge_name: str) -> str:
        return self.finish_notification.format(number=challenge_num, name=challenge_name)

    def get_winner_notification(self, challenge_name: str) -> str:
        return self.winner_notification.format(name=challenge_name)

    def get_progress_notification(self, challenge_name: str, winner_nickname: str, timestamp: datetime) -> str:
        return self.progress_notification.format(
            name=challenge_name, nick_name=winner_nickname, timestamp=timestamp.strftime("%H:%M:%S %d-%m-%Y")
        )

    def get_next_answer_notification(self, question: str, question_num: int) -> str:
        return self.next_answer_notification.format(question=question, number=question_num)

    def get_challenge_info(self, challenges: Sequence[ChallengeInfo], winners_dict: Dict[int, str]) -> str:
        results = ""
        for challenge_num in winners_dict:
            results += (
                f"{self.results_row.format(number=challenge_num, name=challenges[challenge_num].name)} "
                f"@{', @'.join(winners_dict[challenge_num])}"
            )
        return results

    def get_end_info(self, challenges: Sequence[ChallengeInfo], winners_dict: Dict[int, str]) -> str:
        if len(challenges) != len(winners_dict.keys()):
            raise NotEqualChallengesAmount(
                "Challenges list length is not equal to length of challenge numbers in winners_dict!"
            )
        return self.end_info.format(results=self.get_challenge_info(challenges=challenges, winners_dict=winners_dict))


class DataBaseSettings(BaseSettings):
    url: SAURL = 'postgresql://postgres:postgres@localhost/quiz-bot'
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
        from quiz_bot.db.base import metadata

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
