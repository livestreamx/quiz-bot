from typing import TypeVar, Union

from quiz_bot.entity.objects import RegularChallengeInfo, StoryChallengeInfo

TChallengeInfo = TypeVar('TChallengeInfo', RegularChallengeInfo, StoryChallengeInfo)
AnyChallengeInfo = Union[RegularChallengeInfo, StoryChallengeInfo]
