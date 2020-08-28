from pathlib import Path
from typing import Optional
from uuid import uuid4

import matplotlib.pyplot as plt
from quiz_bot.storage import MessageStorage
from wordcloud import WordCloud, wordcloud

_JPG_FMT = "jpg"


class CloudMaker:
    def __init__(self, wordcloud: WordCloud, storage: MessageStorage):
        self._wordcloud_factory = wordcloud
        self._storage = storage

    @staticmethod
    def _generate_picture_name() -> str:
        return f"f{str(uuid4())}.{_JPG_FMT}"

    @property
    def _cloud(self) -> Optional[wordcloud]:
        texts = [message.text for message in self._storage.messages]
        if texts:
            return self._wordcloud_factory.generate(" ".join(texts))
        return None

    def save_cloud(self, folder: Path) -> str:
        picture_name = self._generate_picture_name()
        plt.imshow(self._cloud, interpolation='bilinear')
        plt.axis("off")
        plt.savefig((folder / picture_name).as_posix(), format=_JPG_FMT, dpi=115)
        return picture_name
