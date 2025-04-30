import calendar
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# Задаём год и месяц
YEAR = 2025
MONTH = 4  # Апрель

# Параметры изображения
IMG_WIDTH = 800
IMG_HEIGHT = 600

# Отступы и размеры ячеек
MARGIN_TOP = 100
MARGIN_LEFT = 50
CELL_WIDTH = 80
CELL_HEIGHT = 80
SPACING_X = 20
SPACING_Y = 20

# Путь к шрифту, поддерживающему эмодзи (например, Noto Color Emoji)
FONT_PATH = "path/to/your/emoji-font.ttf"
FONT_SIZE = 40

# Словарь с эмодзи для каждого дня
emoji_map = {
    1: "😃", 2: "🚀", 3: "🤔", 4: "😎", 5: "🏆",
    6: "🍕", 7: "🌟", 8: "🚗", 9: "🚴", 10: "🏅",
    11: "😴", 12: "🍔", 13: "📚", 14: "💻", 15: "🧩",
    16: "🏠", 17: "🥑", 18: "🚜", 19: "💡", 20: "🚗",
    21: "⚽", 22: "🎸", 23: "🎉", 24: "🔥", 25: "🌈",
    26: "🦄", 27: "🍩", 28: "🌳", 29: "🌸", 30: "⏰"
}

# Создаём белый холст
img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), color="white")
draw = ImageDraw.Draw(img)

# Загружаем шрифт для текста и эмодзи
try:
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
except IOError:
    font = ImageFont.load_default()

# Рисуем заголовок: название месяца и год
title_text = f"{calendar.month_name[MONTH]} {YEAR}"
title_font_size = 50
try:
    title_font = ImageFont.truetype(FONT_PATH, title_font_size)
except IOError:
    title_font = ImageFont.load_default()

# Вычисляем размер заголовка с помощью textbbox
bbox = draw.textbbox((0, 0), title_text, font=title_font)
title_width = bbox[2] - bbox[0]
title_height = bbox[3] - bbox[1]

draw.text(
    ((IMG_WIDTH - title_width) / 2, 20),
    title_text,
    font=title_font,
    fill="black"
)

# Получаем календарь месяца в виде списка недель (каждая неделя – список дней)
cal = calendar.Calendar(firstweekday=0).monthdayscalendar(YEAR, MONTH)

# Рисуем ячейки календаря
for week_index, week in enumerate(cal):
    for day_index, day in enumerate(week):
        if day == 0:
            continue  # Пропускаем дни, не принадлежащие текущему месяцу

        # Координаты ячейки
        x = MARGIN_LEFT + day_index * (CELL_WIDTH + SPACING_X)
        y = MARGIN_TOP + week_index * (CELL_HEIGHT + SPACING_Y)

        # Рисуем прямоугольник для ячейки
        draw.rectangle(
            [x, y, x + CELL_WIDTH, y + CELL_HEIGHT],
            outline="grey",
            width=1
        )

        # Получаем эмодзи для дня (если не найдено — используем запасной смайлик)
        day_emoji = emoji_map.get(day, "🙂")
        text_to_draw = day_emoji

        # Вычисляем размеры текста с помощью textbbox
        bbox = draw.textbbox((0, 0), text_to_draw, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Центрируем текст внутри ячейки
        text_x = x + (CELL_WIDTH - text_width) / 2
        text_y = y + (CELL_HEIGHT - text_height) / 2

        draw.text((text_x, text_y), text_to_draw, font=font, fill="black")

# Сохраняем изображение
output_path = "calendar.png"
img.save(output_path)
print(f"Календарь сохранён в {output_path}")
