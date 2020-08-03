class NotSupportedCallbackError(RuntimeError):
    pass


class UserIsNotWinnerError(RuntimeError):
    pass


class ChallengeNotFoundError(RuntimeError):
    pass


class NullableCurrentChallengeError(RuntimeError):
    pass


class UnexpectedQuizStateError(RuntimeError):
    pass
