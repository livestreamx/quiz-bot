from typing import Optional

from quiz_bot.clients import BotResponse, RemoteBotClient
from quiz_bot.entity import InfoSettings
from quiz_bot.quiz import UserMarkupMaker
from quiz_bot.quiz.challenge import ChallengeMaster
from quiz_bot.storage import IUserStorage


class QuizNotifier:
    def __init__(
        self,
        user_storage: IUserStorage,
        remote_client: RemoteBotClient,
        settings: InfoSettings,
        markup_maker: UserMarkupMaker,
        challenge_master: ChallengeMaster,
    ) -> None:
        self._user_storage = user_storage
        self._remote_client = remote_client
        self._settings = settings
        self._markup_maker = markup_maker
        self._challenge_master = challenge_master

    def notify(self, challenge_id: Optional[int], is_start: bool = False) -> None:
        challenge_info = self._challenge_master.get_challenge_info(challenge_id)

        replies = [challenge_info]
        markup = None
        if is_start:
            replies.append(self._settings.wait_for_user_info)
            markup = self._markup_maker.start_markup

        for user in self._user_storage.users:
            response = BotResponse(user=user, replies=replies, markup=markup)
            self._remote_client.send(response)
