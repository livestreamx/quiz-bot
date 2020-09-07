import enum
import logging
import re
from copy import copy
from typing import List, Match, Optional, Sequence

import telebot
from quiz_bot.entity import CheckedResult, ContextChallenge, ContextParticipant, StoryChallengeInfo
from quiz_bot.entity.objects import StoryItem
from quiz_bot.quiz.checkers.base_checker import BaseResultChecker

logger = logging.getLogger(__name__)


class StoryPatternDelimiter(str, enum.Enum):
    LEFT = "{"
    RIGHT = "}"


class StoryPattern(enum.Enum):
    USERNAME = re.compile(rf"({StoryPatternDelimiter.LEFT}username{StoryPatternDelimiter.RIGHT})+")


class AnswerMatchingMixin:
    @staticmethod
    def _prepare_for_matching(text: str) -> List[str]:
        return [x for x in text.strip().lower().split("\n") if x]

    @classmethod
    def _search(cls, answer: str, expectation: str, allow_pattern_parsing: bool = False) -> Optional[Match[str]]:
        result = copy(answer)
        if allow_pattern_parsing:
            for pattern in list(StoryPattern):
                result = pattern.value.sub(expectation, result)
        return re.search(rf"({expectation})+", result, re.I)

    @staticmethod
    def _lines_number_equal(answer_lines: Sequence[str], expected_items: Sequence[StoryItem]) -> bool:
        lines_len = len(answer_lines)
        items_len = len(expected_items)
        if lines_len != items_len:
            logger.debug(
                "Not equal number of user lines and expected items: %s against %s!", lines_len, items_len,
            )
            return False
        return True

    @classmethod
    def _match(cls, answer: str, items: Sequence[StoryItem]) -> bool:
        lines = cls._prepare_for_matching(answer)
        if not cls._lines_number_equal(lines, items):
            return False
        for line_num, line_value in enumerate(lines):
            if all(
                (
                    cls._search(line_value, items[line_num].step.value),
                    cls._search(line_value, items[line_num].construction),
                    cls._search(line_value, items[line_num].text),
                )
            ):
                continue
            return False
        return True


class StoryResultChecker(BaseResultChecker[StoryChallengeInfo], AnswerMatchingMixin):
    def check_answer(
        self,
        participant: ContextParticipant,
        data: ContextChallenge,
        info: StoryChallengeInfo,
        message: telebot.types.Message,
    ) -> CheckedResult:
        current_result = self._result_storage.get_last_result(participant_id=participant.id)
        if not self._match(answer=message.text, items=info.items):
            logger.debug(
                "User '%s' given incorrect story for challenge %s",
                participant.user.nick_name,
                current_result.phase,
                data.id,
            )
            return CheckedResult(correct=False, finish_condition_reached=False, next_phase=current_result.phase)

        logger.info(
            "User '%s' given CORRECT story for challenge %s", participant.user.nick_name, current_result.phase, data.id,
        )
        return self._next_result(participant=participant, data=data, current_result=current_result,)
