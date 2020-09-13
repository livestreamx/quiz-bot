class NotSupportedCallbackError(RuntimeError):
    pass


class ChallengeNotFoundError(RuntimeError):
    pass


class UnexpectedQuizStateError(RuntimeError):
    pass


class UnreachableMessageProcessingError(RuntimeError):
    pass


class NullableParticipantError(RuntimeError):
    pass
