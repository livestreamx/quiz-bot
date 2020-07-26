class NotEqualChallengesAmount(RuntimeError):
    pass


class UnexpectedChallengeNameError(RuntimeError):
    pass


class NoActualChallengeError(RuntimeError):
    pass


class StopChallengeIteration(RuntimeError):
    pass


class NoResultFoundError(RuntimeError):
    pass
