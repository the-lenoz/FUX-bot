import re
from typing import List

NEWLINE = '\n'

def _split_oversized_block(block: str, max_length: int) -> List[str]:
    """
    Вспомогательная функция для разделения одного блока, который сам по себе
    длиннее max_length.

    - Для блоков кода: делит построчно, оборачивая каждый новый чанк в ```.
    - Для остального текста: делит по словам.
    """
    # 1. Проверяем, является ли блок кодом
    # Мы ищем ``` в начале строки, возможно с указанием языка
    if block.startswith("```") and block.endswith("```"):
        # Извлекаем содержимое и "шапку" (e.g., ```python)
        lines = block.split('\n')
        header = lines[0]
        footer = "```"
        content_lines = lines[1:-1]

        chunks = []
        current_chunk_lines = []
        # Вычитаем длину шапки, подвала и двух символов \n
        content_max_length = max_length - len(header) - len(footer) - 2

        for line in content_lines:
            # Если добавление новой строки превысит лимит
            current_content = "\n".join(current_chunk_lines)
            if len(current_content) + len(line) + 1 > content_max_length:
                if current_chunk_lines:
                    chunks.append(f"{header}\n{current_content}\n{footer}")
                    current_chunk_lines = []

            # Если одна строка кода длиннее всего доступного места (редкий случай)
            if len(line) > content_max_length:
                # Принудительно режем строку, сохраняя предыдущий накопленный чанк
                if current_chunk_lines:
                    chunks.append(f"{header}\n{NEWLINE.join(current_chunk_lines)}\n{footer}")
                    current_chunk_lines = []

                for i in range(0, len(line), content_max_length):
                    sub_line = line[i:i + content_max_length]
                    chunks.append(f"{header}\n{sub_line}\n{footer}")
            else:
                current_chunk_lines.append(line)

        if current_chunk_lines:
            chunks.append(f"{header}\n{NEWLINE.join(current_chunk_lines)}\n{footer}")

        return chunks

    # 2. Для обычного текста делим по словам (как в старом коде)
    words = block.split(' ')
    chunks = []
    current_chunk = ""
    for word in words:
        if len(current_chunk) + len(word) + 1 > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = ""

        # Если само слово длиннее лимита
        if len(word) > max_length:
            # Сначала добавляем накопленный чанк
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            # Затем режем слово
            for i in range(0, len(word), max_length):
                chunks.append(word[i:i + max_length])
        else:
            current_chunk += f"{word} "

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def split_markdown_message(text: str, max_length: int = 4096) -> List[str]:
    """
    Разделяет длинное сообщение с Markdown-разметкой на несколько частей.

    Стратегия:
    1.  Разделить текст на логические блоки (параграфы, блоки кода, списки),
        используя в качестве разделителя пустые строки (`\n\n`).
    2.  Собирать блоки в одно сообщение, пока не будет достигнут `max_length`.
    3.  Если очередной блок не помещается, начать новое сообщение с него.
    4.  Если один-единственный блок сам по себе длиннее `max_length`,
        применить к нему специальную логику разделения (см. `_split_oversized_block`).

    Args:
        text: Длинная строка для разделения.
        max_length: Максимальная длина одного сообщения. Для Telegram это 4096.

    Returns:
        Список строк, готовых к отправке.
    """
    if not text:
        return [""]

    # Используем regex для разделения по двум и более переводам строки,
    # что является стандартным разделителем блоков в Markdown.
    # text.strip() убирает пустые строки в начале и конце.
    blocks = re.split(r'\n{2,}', text.strip())

    messages = []
    current_message = ""

    for block in blocks:
        # Если блок сам по себе превышает лимит
        if len(block) > max_length:
            # Сначала добавляем то, что уже накоплено
            if current_message:
                messages.append(current_message)
                current_message = ""
            # Затем делим "негабаритный" блок и добавляем его части
            messages.extend(_split_oversized_block(block, max_length))
            continue

        # Проверяем, поместится ли новый блок в текущее сообщение
        # (+2 за `\n\n` для соединения блоков)
        if current_message and len(current_message) + len(block) + 2 > max_length:
            messages.append(current_message)
            current_message = block
        else:
            if not current_message:
                current_message = block
            else:
                current_message += f"\n\n{block}"

    # Не забываем добавить последнее собранное сообщение
    if current_message:
        messages.append(current_message)

    return messages