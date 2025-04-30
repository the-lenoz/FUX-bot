import secrets
import string

from db.repository import referral_system_repository

# Общий алфавит: заглавные латинские буквы + цифры
ALPHABET = string.ascii_uppercase + string.digits


async def generate_single_promo_code(code_length: int = 10) -> str:
    """
    Генерирует один новый промокод длиной code_length, гарантированно не совпадающий
    с любым кодом в existing_codes. Новый код сразу добавляется в existing_codes.

    :param existing_codes: множество уже существующих промокодов
    :param code_length: длина генерируемого кода
    :return: уникальный промокод (строка)
    """
    existing_codes = await referral_system_repository.select_all_promo_codes()
    # print("\n\n\n\n\n")
    # print(existing_codes)
    # print("\n\n\n\n\n")
    while True:
        # Генерируем случайный код
        code = ''.join(secrets.choice(ALPHABET) for _ in range(code_length))
        # Проверяем, что он не содержится в set
        if code not in existing_codes:
            # Добавляем в множество, чтобы в дальнейшем код не повторился
            return code