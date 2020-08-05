import logging
import socket
from random import choice
from typing import List, Optional

from pydantic import BaseSettings, conint, validator
from quiz_bot.entity.objects import ChallengeInfo, ExtendedChallenge, WinnerResult
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
    filter_phrases: List[str] = []

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
    greetings: str = (
        "Мое имя - <b>T-Quiz Bot</b>. @livestream_x создал меня для того, чтобы я выполнял функцию ведущего для "
        "проведения викторин."
    )
    unknown_info: str = "Если хочешь узнать, что я за бот такой - нажми на <b>кнопку помощи</b>."

    not_started_info: str = "Следующее испытание еще не началось. Ожидайте объявления начала испытания."
    wait_for_user_info: str = "Чтобы начать свой путь к вершине победы, нажми на старт!"
    out_of_date_info: str = "Увы, но вы чуть-чуть припозднились. Испытание было завершено."
    post_end_info: str = "Викторина завершена, спасибо за участие!"

    empty_messages: List[str] = [
        "Нечего сказать " + r'¯\_(ツ)_/¯',
        "Действительно так думаете?",
        "Может быть, в другой раз повезет.",
        "Хмм...",
        "Это, конечно, интересно.",
        "Интересно.",
    ]
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

    @property
    def random_empty_message(self) -> str:
        return choice(self.empty_messages)

    @property
    def random_correct_answer_notification(self) -> str:
        return choice(self.correct_answer_notifications)

    @property
    def random_incorrect_answer_notification(self) -> str:
        return choice(self.incorrect_answer_notifications)


class ChallengeSettings(BaseSettings):
    autostart: bool = False
    challenges: List[ChallengeInfo]

    start_notification: str = "Для тебя начинается испытание #<b>{number}</b> <b>{name}</b>! <i>{description}</i>"
    winner_notification: str = "Мои поздравления - вы стали победителем в испытании '<b>{name}</b>'!"
    prizer_notification: str = "Ура! Ты - призер (#{number} место) в испытании '<b>{name}</b>'."

    next_answer_notification: str = "Вопрос #<b>{number}</b>: {question}"

    challenge_info: str = "Испытание #<b>{number}</b>: <b>{name}</b>\n\n{results}"
    results_row: str = "#{winner_pos} место: @{nick_name} (<code>{timestamp}</code>)"
    time_info: str = "Осталось <code>{minutes}</code> минут до окончания испытания."
    time_over_info: str = "Испытание завершено в <code>{timestamp}</code>."

    @property
    def challenge_amount(self) -> int:
        return len(self.challenges)

    def get_challenge_model(self, number: int) -> ChallengeInfo:
        return self.challenges[number - 1]

    def get_start_notification(self, challenge_num: int, challenge_name: str, description: str) -> str:
        return self.start_notification.format(number=challenge_num, name=challenge_name, description=description)

    def get_winner_notification(self, challenge_name: str, winner_pos: int) -> str:
        if winner_pos > 1:
            return self.prizer_notification.format(name=challenge_name, number=winner_pos)
        return self.winner_notification.format(name=challenge_name)

    def get_next_answer_notification(self, question: str, question_num: int) -> str:
        return self.next_answer_notification.format(question=question, number=question_num)

    def get_results_info(self, winner_results: List[WinnerResult]) -> List[str]:
        results: List[str] = []
        for winner in winner_results:
            results.append(
                self.results_row.format(
                    winner_pos=winner.position,
                    nick_name=winner.user.nick_name,
                    timestamp=winner.finished_at.strftime("%H:%M:%S, %d-%m-%Y"),
                )
            )
        return results

    def get_challenge_info(self, challenge: ExtendedChallenge, winner_results: List[WinnerResult]) -> str:
        info = ""
        if winner_results:
            info += "\n".join(self.get_results_info(winner_results)) + "\n\n"
        if not challenge.finished:
            info += self.time_info.format(minutes=round(challenge.finish_after.total_seconds() / 60))
        else:
            info += self.time_over_info.format(timestamp=challenge.data.finished_at.strftime("%H:%M:%S %d-%m-%Y"))
        return self.challenge_info.format(number=challenge.number, name=challenge.info.name, results=info)


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
