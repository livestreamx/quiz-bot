from quiz_bot.clients import RemoteBotClient
from quiz_bot.manager.challenge import ChallengeMaster
from quiz_bot.storage import IUserStorage


class QuizNotifier:
    def __init__(
        self, user_storage: IUserStorage, remote_client: RemoteBotClient, challenge_master: ChallengeMaster,
    ) -> None:
        self._user_storage = user_storage
        self._remote_client = remote_client
        self._challenge_master = challenge_master

    def notify(self, challenge_id: int) -> None:
        challenge_info = self._challenge_master.get_challenge_info(challenge_id)
        for user in self._user_storage.users:
            self._remote_client.send(user=user, bot_answers=[challenge_info])
