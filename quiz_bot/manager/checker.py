import telebot
from quiz_bot.manager.objects import CheckedResult
from quiz_bot.settings import ChallengeSettings
from quiz_bot.storage import ContextUser, CurrentChallenge, IResultStorage


class ResultChecker:
    def __init__(self, result_storage: IResultStorage, challenge_settings: ChallengeSettings):
        self._result_storage = result_storage
        self._challenge_settings = challenge_settings

    @staticmethod
    def _match(answer: str, expectation: str) -> bool:
        return answer.lower() == expectation.lower()  # TODO: сделать умное сравнение

    def check_answer(
        self, user: ContextUser, current_challenge: CurrentChallenge, message: telebot.types.Message
    ) -> CheckedResult:
        current_result = self._result_storage.get_last_result(user=user)
        expectation = current_challenge.info.answers[current_result.phase]
        if not self._match(answer=message.text, expectation=expectation):
            return CheckedResult(correct=False, challenge_finished=False)

        self._result_storage.finish_phase(current_result)
        if current_result.phase == current_challenge.data.phase_amount:
            return CheckedResult(correct=True, challenge_finished=True)

        self._result_storage.prepare_next_result(result=current_result)
        return CheckedResult(correct=True, challenge_finished=False)
