import logging
import socket
from datetime import datetime
from random import choice
from typing import Dict, List, Optional, Sequence

from pydantic import BaseSettings, conint, validator
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
    url: Optional[URL]
    read_timeout: int = 3

    filter_phrases: List[str] = [
        "совет дня",
        "дать совет",
        "вопрос дня",
        "деньги",
        "деньгах",
        "олег",
        "позвать человека",
        "сделает вашу жизнь проще",
        "учусь",
        "скажите",
        "спросите",
        "отвечать на любые вопросы",
        "моя мечта",
        "мой искусственный интеллект",
        "честно — не знаю",
        "я в тупике",
        "уйти от ответа",
        "не знаю как",
        "отвечу на это",
    ]

    @validator('url', pre=True)
    def make_url(cls, v: Optional[str]) -> Optional[URL]:
        if v is not None and isinstance(v, str):
            return URL(v)
        return v

    class Config:
        env_prefix = 'CHITCHAT_'


class RemoteClientSettings(BaseSettings):
    token: str
    threads_num: conint(ge=1) = 2  # type: ignore

    class Config:
        env_prefix = 'REMOTE_'


class InfoSettings(BaseSettings):
    empty_messages: List[str] = [
        "Нечего сказать " + r'¯\_(ツ)_/¯',
        "Действительно так думаете?",
        "Может быть, в другой раз повезет.",
        "Хмм...",
        "Это, конечно, интересно.",
        "Интересно.",
    ]
    greetings: str = (
        "Мое имя - <b>T-Quiz QuizBot</b>. @livestream_x создал меня для того, чтобы я выполнял функцию ведущего для "
        "проведения викторин. Чтобы начать свой путь к вершине победы, нажми на кнопку старта."
    )
    unknown_info: str = "Если хочешь узнать, что я за бот такой - нажми на <b>кнопку помощи</b>."

    @property
    def random_empty_message(self) -> str:
        return choice(self.empty_messages)


class ChallengeSettings(BaseSettings):
    challenges: List[ChallengeInfo]

    start_notification: str = "Начинается испытание #<b>{number}</b> <b>{name}</b>. <i>{description}</i>"
    finish_notification: str = "Завершено испытание #<b>{number}</b>: <b>{name}</b>."
    winner_notification: str = "Мои поздравления - вы стали победителем в испытании '<b>{name}</b>'!"
    progress_notification: str = "В испытании '{name}' - победитель @{nick_name} ({timestamp})."

    correct_answer_notifications: List[str] = ["Верно.", "Молодец!", "Так держать!", "И, правда, так."]
    incorrect_answer_notifications: List[str] = [
        "Но ответ неверный.",
        "Однако, нет, ответ неправильный.",
        "И в этот раз не получилось попасть в ответ.",
        "...в общем, не правильно 😔",
        "Еще попытка?",
        "Как насчет еще раз попытаться?",
        "Я бы сказал, что вы победили - но вы не победили. Еще раз?",
        "Надо бы попытаться снова попробовать дать ответ.",
        "Наверное, в параллельной вселенной это бы было правильным ответом. Но в нашей - увы.",
    ]
    next_answer_notification: str = "Вопрос #<b>{number}</b>: {question}"

    end_info: str = "Итоги викторины:\n{results}\n\nВикторина завершена, спасибо за участие!"
    results_row: str = "Испытание #<b>{number}</b> '<b>{name}</b>': "
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
    url: SAURL = 'postgresql://postgres:postgres@localhost:6432/quiz-bot'
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
