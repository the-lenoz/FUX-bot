import datetime


def get_now_utc_time():
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)