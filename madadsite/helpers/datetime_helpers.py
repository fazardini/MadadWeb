import pytz
from datetime import datetime


TEHRAN_TZ = pytz.timezone("Asia/Tehran")


def the_today():
    return datetime.now(tz=TEHRAN_TZ).date()
