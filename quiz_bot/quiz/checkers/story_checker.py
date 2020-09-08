import enum
import logging
import re
from typing import Dict, List, Match, Optional, Pattern, Sequence

import telebot
from quiz_bot.entity import (
    CheckedResult,
    ContextChallenge,
    ContextParticipant,
    StoryChallengeInfo,
    StoryItem,
    StoryPatternValue,
)
from quiz_bot.quiz.checkers.base_checker import BaseResultChecker

logger = logging.getLogger(__name__)


class StoryPatternDelimiter(str, enum.Enum):
    LEFT = "{"
    RIGHT = "}"


def _compile_pattern(keyword: str) -> Pattern[str]:
    return re.compile(rf"({StoryPatternDelimiter.LEFT}{keyword}{StoryPatternDelimiter.RIGHT})+")


_KEYWORD_TO_PATTERN_MAPPING: Dict[StoryPatternValue, Pattern[str]] = {
    x: _compile_pattern(x.value) for x in list(StoryPatternValue)
}


class AnswerMatchingMixin:
    @staticmethod
    def _prepare_for_matching(text: str) -> List[str]:
        return [x for x in text.strip().lower().split("\n") if x]

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

    @staticmethod
    def _replace_patterns(answer: str, participant: ContextParticipant) -> None:
        for key, value in _KEYWORD_TO_PATTERN_MAPPING.items():
            if key is StoryPatternValue.USERNAME:
                answer = value.sub(participant.user.nick_name, answer)

    @classmethod
    def _search(cls, answer: str, expectation: str) -> Optional[Match[str]]:
        return re.search(rf"({expectation})+", answer, re.I)

    @classmethod
    def _match(cls, answer: str, items: Sequence[StoryItem], participant: ContextParticipant) -> bool:
        cls._replace_patterns(answer=answer, participant=participant)
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
        if not self._match(answer=message.text, items=info.items, participant=participant):
            logger.debug(
                "User '%s' given incorrect story for challenge %s", participant.user.nick_name, data.id,
            )
            return CheckedResult(correct=False, finish_condition_reached=False, next_phase=current_result.phase)

        logger.info(
            "User '%s' given CORRECT story for challenge %s", participant.user.nick_name, current_result.phase, data.id,
        )
        return self._next_result(participant=participant, data=data, current_result=current_result,)
