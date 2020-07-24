class PreviousChallengeNotFinishedError(RuntimeError):
    pass


class NotEqualChallengesAmount(RuntimeError):
    pass


class UnexpectedChallengeNameError(RuntimeError):
    pass


class NoActualChallengeError(RuntimeError):
    pass


class StopChallengeIteration(StopIteration):
    pass


class NoResultFoundError(RuntimeError):
    pass
