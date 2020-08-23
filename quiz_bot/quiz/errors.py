class NotSupportedCallbackError(RuntimeError):
    pass


class ChallengeNotFoundError(RuntimeError):
    pass


class NullableCurrentChallengeError(RuntimeError):
    pass


class UnexpectedQuizStateError(RuntimeError):
    pass


class UnreachableMessageProcessingError(RuntimeError):
    pass


class UnexpectedChallengeStateError(RuntimeError):
    pass


class NullableParticipantError(RuntimeError):
    pass
