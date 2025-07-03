import calendar
import io
import logging
import os
import random
import secrets
from datetime import timedelta, date, datetime
from io import BytesIO
from statistics import fmean
from typing import Literal, List

import matplotlib.pyplot as plt
from PIL import Image, ImageFont, ImageDraw
from aiogram.types import BufferedInputFile

from bots import main_bot
from data.keyboards import buy_sub_keyboard, get_rec_keyboard
from db.repository import days_checkups_repository, users_repository
from settings import calendar_template_photo
from utils.subscription import check_is_subscribed

# Цвета
ORANGE_COLOR = (254, 110, 0)
GRAY_COLOR = (50, 50, 50)
BLACK_COLOR = (13, 20, 13)
DAY_BOX_BG = (255, 255, 255)
DAY_BOX_BORDER = ORANGE_COLOR
DAY_BOX_DONE_BG = (255, 239, 203)
CROSS_COLOR = (200, 200, 200)

# Отступы и координаты (рассчитаны для холста 1080x1080)
PADDING = 60
SUBTITLE_Y = 150
ORANGE_BAR_Y = 330
ORANGE_BAR_HEIGHT = 80
DAYS_GRID_Y_START = 480  # Y-координата для начала отрисовки ячеек дней

# Размеры сетки
CELL_SIZE = 90
CELL_SPACING_HORIZONTAL = 49
CELL_SPACING_VERTICAL = 45
GRID_WIDTH = 7 * CELL_SIZE + 6 * CELL_SPACING_HORIZONTAL
GRID_START_X = (1330 - GRID_WIDTH) / 2
CELL_RADIUS = 20
CELL_INTERIOR_PADDING = 30

DAY_NUMBER_TEXT_NEGATIVE_PADDING = 14

trophy_image = Image.open("assets/trophy.png").resize((40, 40))


# Шрифты Roboto
try:
    FONT_PATH_BOLD = "assets/fonts/Roboto-Bold.ttf"
    FONT_PATH_REGULAR = "assets/fonts/Roboto-Regular.ttf"
    font_subtitle = ImageFont.truetype(FONT_PATH_BOLD, 72)
    font_month_header = ImageFont.truetype(FONT_PATH_BOLD, 56)
    font_day_num = ImageFont.truetype(FONT_PATH_REGULAR, 22)
    font_week_avg = ImageFont.truetype(FONT_PATH_BOLD, 32)
except IOError:
    print("Шрифты Roboto-Bold.ttf и Roboto-Regular.ttf не найдены. Используются шрифты по умолчанию.")
    font_subtitle = ImageFont.load_default()
    font_month_header = ImageFont.load_default()
    font_day_num = ImageFont.load_default()
    font_week_avg = ImageFont.load_default()

# Локализация
MONTH_NAMES_RU = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь",
    7: "Июль", 8: "Август", 9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}
MONTH_NAMES_RU_CAPS = {k: v.upper() for k, v in MONTH_NAMES_RU.items()}


def generate_emotion_chart(emotion_data=None, dates=None, checkup_type: Literal["emotions", "productivity"] | None = None):
    """
    Принимает список эмоций (от 1 до 5) длиной 7 элементов.
    Возвращает график в виде bytes (для отправки через Telegram-бота).
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

    # Сохраняем в буфер
    buffer = io.BytesIO()
    img.convert('RGB').save(buffer, format='PNG')
    buffer.seek(0)

    # Удаляем временный файл
    if os.path.exists(temp_filename):
        os.remove(temp_filename)

    return buffer.getvalue()


def generate_tracking_calendar(year: int, month: int, checkup_type: Literal["emotions", "productivity"], data: List[int]) -> bytes:
    """
    Дорисовывает на готовом шаблоне календарь на указанный месяц и год,
    используя шрифт Roboto и фиксированные координаты.

    Предполагаемый размер шаблона: 1080x1080 пикселей.

    Args:
        :param year: Год (например, 2025)
        :param month: Месяц (1-12).
        :param data:
        :param checkup_type:

    Returns:
        bytes - буфер, содержащий изображение календаря

    """
    # Создаем копию, чтобы не изменять оригинальное изображение
    img = calendar_template_photo.copy()
    draw = ImageDraw.Draw(img)

    # --- 2. Отрисовка недостающих элементов ---

    # Подзаголовок (название месяца и год)
    # Шаблон уже содержит "ТВОЙ ОТЧЁТ ЗА МЕСЯЦ", мы добавляем дату под ним
    subtitle_text = f"{MONTH_NAMES_RU[month]}, {year} г."
    subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=font_subtitle)
    subtitle_x = (1340 - subtitle_bbox[2]) / 2  # Выравнивание по центру
    draw.text((subtitle_x, SUBTITLE_Y), subtitle_text, font=font_subtitle, fill=ORANGE_COLOR)

    # Название месяца в оранжевой плашке
    month_header_text = MONTH_NAMES_RU_CAPS[month]
    month_header_bbox = draw.textbbox((0, 0), month_header_text, font=font_month_header)
    draw.text(
        ((1340 - month_header_bbox[2]) / 2, ORANGE_BAR_Y + (ORANGE_BAR_HEIGHT - month_header_bbox[3]) / 2),
        month_header_text, font=font_month_header, fill=DAY_BOX_BG
    )

    # Ячейки с днями
    # Шаблон уже содержит "ПН, ВТ, ...", мы рисуем сетку под ними
    cal = calendar.monthcalendar(year, month)
    top_value = 0
    top_y = 0

    for week_idx, week in enumerate(cal):
        y = DAYS_GRID_Y_START + week_idx * (CELL_SIZE + CELL_SPACING_VERTICAL)
        last_week_day = 0
        last_week_length = 0
        for day_idx, day in enumerate(week):
            if day != 0:
                last_week_day = day
                last_week_length += 1

                x = GRID_START_X + day_idx * (CELL_SIZE + CELL_SPACING_HORIZONTAL)




                # Рисуем номер дня
                day_str = str(day)
                day_num_bbox = draw.textbbox((0, 0), day_str, font=font_day_num)
                draw.text((x + (CELL_SIZE - day_num_bbox[2]) / 2,
                           y + CELL_SIZE + day_num_bbox[3] - DAY_NUMBER_TEXT_NEGATIVE_PADDING), day_str,
                          font=font_day_num,
                          fill=GRAY_COLOR)

                day_data = data[day - 1] if day <= len(data) else None

                if day_data is None:
                    # Рисуем ячейку
                    draw.rounded_rectangle([(x, y), (x + CELL_SIZE, y + CELL_SIZE)], radius=CELL_RADIUS,
                                           fill=ORANGE_COLOR if day_idx == 6 else DAY_BOX_BG,
                                           outline=DAY_BOX_BORDER)

                    # Рисуем крестик
                    draw.line([(x + CELL_INTERIOR_PADDING, y + CELL_INTERIOR_PADDING),
                               (x + CELL_SIZE - CELL_INTERIOR_PADDING, y + CELL_SIZE - CELL_INTERIOR_PADDING)],
                              fill=CROSS_COLOR, width=5)
                    draw.line([(x + CELL_SIZE - CELL_INTERIOR_PADDING, y + CELL_INTERIOR_PADDING),
                               (x + CELL_INTERIOR_PADDING, y + CELL_SIZE - CELL_INTERIOR_PADDING)],
                              fill=CROSS_COLOR, width=5)
                else:
                    # Рисуем ячейку
                    draw.rounded_rectangle([(x, y), (x + CELL_SIZE, y + CELL_SIZE)], radius=CELL_RADIUS,
                                           fill=ORANGE_COLOR if day_idx == 6 else DAY_BOX_DONE_BG,
                                           outline=DAY_BOX_BORDER)
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

                    emoji_img = Image.open(emoji_levels[day_data])
                    scaled_emoji = emoji_img.resize((70, 70), Image.Resampling.LANCZOS)
                    # Вставляем эмодзи на основное изображение с сохранением прозрачности
                    img.paste(scaled_emoji, (round(x + CELL_INTERIOR_PADDING - 20), round(y + CELL_INTERIOR_PADDING - 20)), scaled_emoji)

        week_data = [d for d in data[max(last_week_day - last_week_length, 0) : last_week_day] if d is not None]
        if week_data and len(week_data) > 2:
            week_avg = round(fmean(week_data) * 2)
            if week_avg > top_value:
                top_value = week_avg
                top_y = y
            week_avg_str = str(week_avg) + "/10"
            week_avg_bbox = draw.textbbox((0, 0), week_avg_str, font=font_week_avg)
            draw.text((1340 - week_avg_bbox[2] - 55,
                       y + CELL_SIZE / 2 - week_avg_bbox[3] / 2), week_avg_str, font=font_week_avg,
                      fill=BLACK_COLOR)

    img.paste(trophy_image, (round(1340 - 45), round(top_y + CELL_SIZE / 2 - 16)), trophy_image)



    buffer = io.BytesIO()
    img.convert('RGB').save(buffer, format='PNG')
    buffer.seek(0)

    return buffer.getvalue()

async def send_weekly_checkup_report(user_id: int, last_date = datetime.now()):
    user = await users_repository.get_user_by_user_id(user_id)
    if not user.received_weekly_tracking_reports or await check_is_subscribed(user_id):
        for checkup_type in ("emotions", "productivity"):
            try:
                checkup_days = await days_checkups_repository.get_days_checkups_by_user_id(user_id=user.user_id)
                checkups_report = []

                send = False
                for weekday in range(7):
                    day = last_date - timedelta(days=last_date.weekday() - weekday)
                    day_checkup_data = None
                    for checkup_day in checkup_days:
                        if checkup_day.creation_date and checkup_day.creation_date.date() == day.date() \
                                and checkup_day.checkup_type == checkup_type:
                            day_checkup_data = checkup_day.points
                            send = True
                    checkups_report.append(day_checkup_data)

                if send:
                    await users_repository.user_got_weekly_reports(user_id=user_id)
                    graphic = generate_emotion_chart(emotion_data=checkups_report,
                                                     dates=["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"],
                                                     checkup_type=checkup_type)
                    await main_bot.send_photo(
                        photo=BufferedInputFile(file=graphic, filename="graphic.png"),
                        chat_id=user.user_id,
                        caption=f"✅ Трекинг <b>{'эмоций' if checkup_type == 'emotions' else 'продуктивности'}</b> за неделю готов!"
                    )
            except Exception as e:
                logging.error(e)
    else:
        await main_bot.send_message(
            user_id,
            "Результаты <i>недельного трекинга</i> готовы, но для того, чтобы их увидеть нужна <b>подписка</b>!",
            reply_markup=get_rec_keyboard(f"tracking-{int(last_date.timestamp())}").as_markup()
        )

async def send_monthly_checkup_report(user_id: int, last_date = datetime.now()):
    if await check_is_subscribed(user_id):
        checkup_type: Literal["emotions", "productivity"]
        for checkup_type in ("emotions", "productivity"):
            try:
                checkup_days = await days_checkups_repository.get_days_checkups_by_user_id(user_id=user_id)
                checkups_report = []

                send = False
                for monthday in range(1, calendar.monthrange(last_date.year, last_date.month)[1] + 1):
                    day = datetime(year=last_date.year, month=last_date.month, day=monthday)
                    day_checkup_data = None
                    for checkup_day in checkup_days:
                        if checkup_day.creation_date and checkup_day.creation_date.date() == day.date() \
                                and checkup_day.checkup_type == checkup_type:
                            day_checkup_data = checkup_day.points
                            send = True
                    checkups_report.append(day_checkup_data)

                if send:
                    await users_repository.user_got_weekly_reports(user_id=user_id)
                    graphic = generate_tracking_calendar(year=last_date.year, month=last_date.month,
                                                         data=checkups_report,
                                                        checkup_type=checkup_type)
                    await main_bot.send_photo(
                        photo=BufferedInputFile(file=graphic, filename="graphic.png"),
                        chat_id=user_id,
                        caption=f"✅ Трекинг <b>{'эмоций' if checkup_type == 'emotions' else 'продуктивности'}</b> за <u>месяц</u> готов!"
                    )
            except Exception as e:
                logging.error(e)
    else:
        await main_bot.send_message(
            user_id,
            "Результаты <i>месячного трекинга</i> готовы, но для того, чтобы их увидеть нужна <b>подписка</b>!",
            reply_markup=get_rec_keyboard(f"tracking-{int(last_date.timestamp())}").as_markup()
        )