from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(HERE, "fonts", "Roboto-VariableFont_wdth,wght.ttf")

def generate_blurred_image_with_text(
    text: str,
    img_width: int = 2000,
    img_height: int = 2000,
    enable_blur: bool = False
) -> bytes:
    """
    Генерирует PNG-картинку (по умолчанию 2000×2000) с динамическим подбором размера шрифта.
    - Текст выравнивается по левому краю.
    - Межстрочный интервал одинаковый для всех строк (убирает "скачки" между строками).
    - В конце картинка (включая текст) при желании полностью размывается (enable_blur=True).
    - Возвращает байты PNG (никакого файла не сохраняет).
    """

    background_color = (255, 239, 213)  # Нежно-кремовый
    image = Image.new('RGB', (img_width, img_height), background_color)
    draw = ImageDraw.Draw(image)

    margin_x = 200
    margin_y = 200

    max_font_size = 200
    min_font_size = 10
    step = 2

    # ---------------------------
    # Старая ваша функция wrap
    # ---------------------------
    def wrap_text_to_width(full_text, used_font, max_allowed_width):
        words = full_text.split()
        if not words:
            return []
        lines_local = []
        current_line = words[0]
        for word in words[1:]:
            test_line = current_line + ' ' + word
            bbox = used_font.getbbox(test_line)
            line_width = bbox[2] - bbox[0]
            if line_width <= max_allowed_width:
                current_line = test_line
            else:
                lines_local.append(current_line)
                current_line = word
        lines_local.append(current_line)
        return lines_local

    def measure_line_height(used_font):
        bbox = used_font.getbbox("Ay")
        return bbox[3] - bbox[1]

    def measure_text_block(lines_list, used_font, line_spacing):
        if not lines_list:
            return (0, 0)
        max_width = 0
        for line_s in lines_list:
            bbox = used_font.getbbox(line_s)
            w_line = bbox[2] - bbox[0]
            if w_line > max_width:
                max_width = w_line
        total_height = len(lines_list) * line_spacing
        return (max_width, total_height)

    # ------------------------------------------------------------
    # Подбор размера шрифта (ЦИКЛ)
    # ------------------------------------------------------------
    chosen_font_size = min_font_size
    max_text_width = img_width - 2 * margin_x

    for size in range(max_font_size, min_font_size - 1, -step):
        try:
            candidate_font = ImageFont.truetype(FONT_PATH, size)
        except OSError:
            candidate_font = ImageFont.load_default()

        # --- ВАЖНО: тут мы СНАЧАЛА разбиваем text по \n, затем оборачиваем ---
        raw_lines = text.splitlines()  # сохраняет пустые строки и переносы
        lines_temp = []
        for raw_line in raw_lines:
            # Если строка пустая (значит просто перенос)
            if not raw_line.strip():
                lines_temp.append("")  # пусть будет одна пустая строка
                continue
            # Иначе обёртываем её по ширине
            wrapped = wrap_text_to_width(raw_line, candidate_font, max_text_width)
            lines_temp.extend(wrapped)

        base_line_height = measure_line_height(candidate_font)
        line_spacing = base_line_height * 1.3

        w_block, h_block = measure_text_block(lines_temp, candidate_font, line_spacing)

        if w_block <= max_text_width and h_block <= (img_height - 2 * margin_y):
            chosen_font_size = size
            break

    # ------------------------------------------------------------
    # Формируем финальный шрифт
    # ------------------------------------------------------------
    final_font = ImageFont.truetype(FONT_PATH, chosen_font_size)

    # --- То же самое: разбиваем text на строки с учётом \n ---
    raw_lines = text.splitlines()
    lines = []
    for raw_line in raw_lines:
        if not raw_line.strip():
            lines.append("")
            continue
        wrapped = wrap_text_to_width(raw_line, final_font, max_text_width)
        lines.extend(wrapped)

    base_line_height = measure_line_height(final_font)
    line_spacing = base_line_height * 1.3

    w_block, h_block = measure_text_block(lines, final_font, line_spacing)
    start_y = (img_height - h_block) // 2

    # ------------------------------------------------------------
    # Рисуем
    # ------------------------------------------------------------
    def draw_bold_text(draw_obj, x, y, content, used_font, fill=(0, 0, 0)):
        offsets = [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]
        for dx, dy in offsets:
            draw_obj.text((x + dx, y + dy), content, font=used_font, fill=fill)

    current_y = start_y
    for line in lines:
        draw_bold_text(draw, margin_x, current_y, line, final_font)
        current_y += line_spacing

    # ------------------------------------------------------------
    # Размываем при необходимости
    # ------------------------------------------------------------
    if enable_blur:
        blur_radius = 15.0
        image = image.filter(ImageFilter.GaussianBlur(blur_radius))

    # ------------------------------------------------------------
    # Возвращаем байты (PNG)
    # ------------------------------------------------------------
    output_stream = io.BytesIO()
    image.save(output_stream, format='PNG')
    output_stream.seek(0)
    return output_stream.read()
