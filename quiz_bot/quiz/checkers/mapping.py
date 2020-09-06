from collections import Mapping
from typing import Type

from quiz_bot.entity import ChallengeType
from quiz_bot.quiz import RegularResultChecker

CHALLENGE_TYPE_TO_CHECKER_MAPPING: Mapping[
    ChallengeType, Type[RegularResultChecker]
] = {  # Union with StoryResultChecker...
    ChallengeType.REGULAR: RegularResultChecker,
}
