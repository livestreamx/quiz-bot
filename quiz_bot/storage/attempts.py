import abc
from typing import Dict


class IAttemptsStorage(abc.ABC):
    @abc.abstractmethod
    def need_to_skip_notify(self, user_id: int) -> bool:
        pass

    @abc.abstractmethod
    def ensure_skip_for_user(self, user_id: int) -> bool:
        pass

    @abc.abstractmethod
    def clear(self, user_id: int) -> None:
        pass


class AttemptsStorage(IAttemptsStorage):
    def __init__(self, skip_notification_attempt_num: int) -> None:
        self._attempt_num = skip_notification_attempt_num
        self._user_attempts: Dict[int, int] = {}

    def need_to_skip_notify(self, user_id: int) -> bool:
        attempts = self._user_attempts.get(user_id)
        if attempts is None:
            self._user_attempts[user_id] = 1
            return False
        self._user_attempts[user_id] += 1
        return attempts == self._attempt_num

    def ensure_skip_for_user(self, user_id: int) -> bool:
        attempts = self._user_attempts.get(user_id)
        if isinstance(attempts, int) and attempts >= self._attempt_num:
            return True
        return False

    def clear(self, user_id: int) -> None:
        self._user_attempts[user_id] = 0
