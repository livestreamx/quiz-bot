import datetime

import pytz


def get_now() -> datetime.datetime:
    return datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)


def display_time(time: datetime.datetime, zone: datetime.tzinfo) -> str:
    return time.astimezone(zone).strftime("%H:%M:%S, %d-%m-%Y")
