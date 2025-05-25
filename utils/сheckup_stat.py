import io
import os
import random
import secrets
import warnings
from datetime import timedelta, date

import matplotlib.pyplot as plt
from PIL import Image, ImageFont

warnings.filterwarnings("ignore", category=UserWarning)

# Try to import Pilmoji if available
try:
    from pilmoji import Pilmoji

    pilmoji_available = True
except ImportError:
    pilmoji_available = False
    print("Pilmoji not installed. Emoji rendering may be limited.")
    print("To install: pip install pilmoji")


def generate_emotion_chart(emotion_data=None, dates=None, checkup_type: str | None = None):
    """
    Принимает список эмоций (от 1 до 5) длиной 7 элементов.
    Возвращает график в виде io.BytesIO (для отправки через Telegram-бота).
    """
    # Для тестирования, если данные не переданы
    if emotion_data is None:
        emotion_data = [random.randint(1, 5) for _ in range(7)]
    if dates is None:
        dates = [(date.today() - timedelta(days=6 - i)).strftime("%m-%d") for i in range(7)]

    assert len(emotion_data) == 7, "Ожидается список из 7 значений (по одному на каждый день недели)"

    # Эмодзи для разных уровней эмоций
    if checkup_type == "emotions":
        emoji_levels = {
            1: "assets/confounded.png",
            2: "assets/unamused.png",
            3: "assets/neutral_face.png",
            4: "assets/relieved.png",
            5: "assets/star-struck.png"
        }
    else:
        emoji_levels = {
            1: "assets/wood.png",  # полено — вообще не движется
            2: "assets/snail.png",  # улитка — очень медленно
            3: "assets/bicycle.png",  # велосипед — средне
            4: "assets/car.png",  # машина — быстро
            5: "assets/rocket.png"  # ракета — очень быстро
        }

    # Создаём фигуру и оси с высоким разрешением
    fig, ax = plt.subplots(figsize=(8, 6), facecolor='#FEEDE1', dpi=200)
    ax.set_facecolor('#FEEDE1')

    # Строим график линии с оранжевыми маркерами
    ax.plot(range(len(dates)),
            emotion_data, marker='o',
            markersize=10,
            color='black',
            markerfacecolor='orangered',
            markeredgecolor='orangered',
            linewidth=2)

    # Настраиваем оси
    ax.set_yticks(list(range(1, 6)))
    ax.set_yticklabels(["" for _ in range(1, 6)])  # Пустые метки, эмодзи добавим позже
    ax.set_xticks(range(len(dates)))

    # Используем переданные даты для подписей оси X
    ax.set_xticklabels(dates, fontsize=12, color='orangered')

    # Выделяем последний день недели (воскресенье)
    for i, label in enumerate(ax.get_xticklabels()):
        if i != len(dates) - 1:
            label.set_bbox(dict(facecolor='white', edgecolor='none', pad=5, boxstyle='round,pad=0.5'))
            label.set_color('orangered')
        else: # Последний день (воскресенье)
            label.set_bbox(dict(facecolor='orangered', edgecolor='none', pad=5, boxstyle='round,pad=0.5'))
            label.set_color('white')


    ax.set_xlim(-0.7, len(dates) - 0.5)
    ax.set_ylim(0.5, 5.5)
    name = 'ТРЕКИНГ ЭМОЦИЙ' if checkup_type == "emotions" else "ТРЕКИНГ ПРОДУКТИВНОСТИ"

    ax.text(0.5, 1.05, name, ha='center', va='center', transform=ax.transAxes,
            fontsize=24, color='orangered', weight='bold')

    # Убираем рамки
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Исправляем размещение "НЕДЕЛЬНЫЙ ОТЧЁТ ГОТОВ!" внизу справа
    # ax.text(0.85, -0.07, 'НЕДЕЛЬНЫЙ ОТЧЁТ ГОТОВ!', ha='right', va='center', transform=ax.transAxes,
    #         fontsize=10, color='orangered', weight='bold')

    # Сохраняем график во временный файл
    temp_filename = f'temp_chart_{secrets.token_hex(32)}.png'
    plt.tight_layout()
    plt.savefig(temp_filename, format='png', bbox_inches='tight', facecolor='#FEEDE1')
    plt.close(fig)

    # Открываем сохранённое изображение с графиком через Pillow
    img = Image.open(temp_filename)
    width, height = img.size

    # Преобразуем в RGBA для поддержки прозрачности
    img = img.convert('RGBA')

    # Пробуем найти подходящий шрифт для эмодзи
    # try:
        # Указываем путь к вашему локальному шрифту
    font_path = os.path.join('utils', 'fonts', 'NotoColorEmoji-Regular.ttf')
    emoji_font = None
    emoji_size = 40
    # Сначала пробуем загрузить локальный шрифт
    try:
        emoji_font = ImageFont.truetype(font_path, emoji_size)
        # print(f"Успешно загружен локальный шрифт: {font_path}")
    except Exception as e:
        # print(f"Критическая ошибка загрузки шрифта: {e}")
        emoji_font = ImageFont.load_default()

    # Получаем координаты для размещения эмодзи на графике
    x_min, x_max = 0.1 * width, 0.9 * width
    y_min, y_max = 0.3 * height, 0.85 * height
    y_step = (y_max - y_min) / 4  # 5 уровней (1-5)

    # Новая логика для размещения эмодзи с правильными цветами
    for level in range(1, 6):
        y_pos = int(y_max - (level - 1) * (y_step * 1.23)) - 40
        x_pos = int(x_min * 0.5 - 60)

        # Создаем отдельное изображение для каждого эмодзи
        emoji_img = Image.open(emoji_levels[level])
        scaled_emoji = emoji_img.resize((90, 90), Image.Resampling.LANCZOS)
        # Вставляем эмодзи на основное изображение с сохранением прозрачности
        img.paste(scaled_emoji, (x_pos, y_pos), scaled_emoji)

    # Добавляем иконку записной книжки в верхний правый угол
    # try:
    #     # Создаем иконку записной книжки
    #     notebook_overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    #     notebook_draw = ImageDraw.Draw(notebook_overlay)
    #
    #     # Позиция для иконки (верхний правый угол)
    #     notebook_x, notebook_y = width * 0.85, height * 0.3
    #
    #     # Рисуем оранжевую рамку блокнота
    #     notebook_width, notebook_height = 50, 70
    #     notebook_draw.rectangle(
    #         [(notebook_x - notebook_width / 2, notebook_y - notebook_height / 2),
    #          (notebook_x + notebook_width / 2, notebook_y + notebook_height / 2)],
    #         outline='orangered', fill=(255, 255, 255, 200), width=3
    #     )
    #
    #     # Добавляем линии на блокноте
    #     line_spacing = 10
    #     for i in range(4):
    #         y = notebook_y - notebook_height / 3 + i * line_spacing
    #         notebook_draw.line(
    #             [(notebook_x - notebook_width / 3, y), (notebook_x + notebook_width / 3, y)],
    #             fill='purple', width=2
    #         )
    #
    #     # Добавляем "скрепку" вверху
    #     clip_color = 'purple'
    #     notebook_draw.rectangle(
    #         [(notebook_x - 5, notebook_y - notebook_height / 2 - 5),
    #          (notebook_x + 5, notebook_y - notebook_height / 2)],
    #         fill=clip_color, outline=None
    #     )
    #
    #     # Объединяем с основным изображением
    #     img = Image.alpha_composite(img, notebook_overlay)

    # except Exception as e:
    #     print(f"Ошибка при создании иконки блокнота: {e}")

    # Сохраняем в буфер
    buffer = io.BytesIO()
    img.convert('RGB').save(buffer, format='PNG')
    buffer.seek(0)

    # Удаляем временный файл
    if os.path.exists(temp_filename):
        os.remove(temp_filename)

    return buffer

#
# if __name__ == "__main__":
#     # Генерируем тестовые данные
#     emotion_data = [1, 3, 2, 3, 4, 2, 5]  # Пример данных как на картинке
#     dates = [(date.today() - timedelta(days=6 - i)).strftime("%m-%d") for i in range(7)]
#
#     # Генерируем график
#     buffer = generate_emotion_chart(emotion_data, dates)
#
#     # Сохраняем для проверки
#     with open("emotion_chart_final.png", "wb") as f:
#         f.write(buffer.getvalue())
#
#     print("График сохранен в файл emotion_chart_final.png")