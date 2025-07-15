import re
from datetime import datetime


async def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if re.match(email_regex, email):
        return True
    else:
        return False


def is_valid_time(time_str: str) -> bool:
    try:
        # Если формат 'HH:MM' некорректен, будет сгенерирован ValueError
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False
