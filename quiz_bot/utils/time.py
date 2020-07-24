import datetime

import pytz


def get_now() -> datetime.datetime:
    return datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
