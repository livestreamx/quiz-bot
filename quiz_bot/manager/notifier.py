from quiz_bot.clients import RemoteBotClient
from quiz_bot.manager.challenge import ChallengeMaster
from quiz_bot.settings import InfoSettings


class QuizNotifier:
    def __init__(
        self, remote_client: RemoteBotClient, info_settings: InfoSettings, challenge_master: ChallengeMaster,
    ) -> None:
        self._remote_client = remote_client
        self._info_settings = info_settings
        self._challenge_master = challenge_master
