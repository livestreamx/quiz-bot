from typing import Union

from quiz_bot.quiz.checkers.regular_checker import RegularResultChecker
from quiz_bot.quiz.checkers.story_checker import StoryResultChecker

AnyResultChecker = Union[RegularResultChecker, StoryResultChecker]
