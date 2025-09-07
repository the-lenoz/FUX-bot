from PIL import Image
from aiogram.types import FSInputFile

calendar_template_photo = Image.open(
    "assets/calendar_template.png"
).resize((1340, 1340))
mental_helper_photo = FSInputFile("assets/mental_helper_photo.jpg")
exercises_photo = FSInputFile("assets/exercises_photo.jpg")
checkups_graphic_photo = FSInputFile("assets/checkups_graphic_photo.jpg")
checkups_types_photo = FSInputFile("assets/checkups_types_photo.jpg")
temperature_ai_photo = FSInputFile("assets/temperature_ai_photo.jpg")
universal_ai_photo = FSInputFile("assets/universal_ai_photo.jpg")
payment_photo = FSInputFile("assets/payment_photo.jpg")
menu_photo = FSInputFile("assets/menu_photo.jpg")
system_setting_photo = FSInputFile("assets/system_setting_photo.jpg")
sub_description_photo_before = FSInputFile("assets/sub_description_photo_before.jpg")
you_fooher_photo = FSInputFile("assets/you_fooher_photo.jpg")
sub_description_photo_after = FSInputFile("assets/sub_description_photo_after.jpg")
how_are_you_photo = FSInputFile("assets/how_are_you_photo.jpg")
checkup_emotions_photo = FSInputFile("assets/checkup_emotions_photo.jpg")
checkup_productivity_photo = FSInputFile("assets/checkup_productivity_photo.jpg")
premium_sub_photo = FSInputFile("assets/premium_sub_photo.jpg")
productivity_emoji_description_photo = FSInputFile("assets/productivity_emoji_description_photo.jpg")
emotions_emoji_description_photo = FSInputFile("assets/emotions_emoji_description_photo.jpg")
emoji_description_photo = FSInputFile("assets/emoji_description_photo.jpg")
photos_pages = {
    1: mental_helper_photo,
    2: exercises_photo,
    3: emoji_description_photo,
    4: checkups_graphic_photo,
    5: temperature_ai_photo,
    6: universal_ai_photo,
    7: sub_description_photo_before,
    8: system_setting_photo
}
