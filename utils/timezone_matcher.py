import datetime

timezones_dict = {
    -1200: "GMT-12",
    -1100: "GMT-11",
    -1000: "GMT-10",
    -900: "GMT-9",
    -800: "🏔️ GMT–8 — Калифорнийский код и кофе на закате",
    -700: "🌊 GMT-7 — Аризона",
    -600: "🌆 GMT-6 — Мексика и Коста-Рика",
    -500: "🌉 GMT–5 — Нью-Йорк зовёт: утро начинается с hustle",
    -400: "🌆 GMT-4 — Венесуэла и Чили",
    -300: "🌍 GMT-3 — Рио-де-Жанейро и Буэнос Айрес",
    -200: "GMT-2",
    -100: "GMT-1",
    0000: "🌍 GMT+0 — Я живу по солнцу",
    100: "🌴 GMT+1 — Европейский баланс и утренний эспрессо",
    200: "🌇 GMT+2 — В ритме Греции и Кипра",
    300: "🌆 GMT+3 — Классика Москвы и Питера",
    400: "🏜️ GMT+4 — Тёплый Дубай и Самара",
    500: "🛤 GMT+5 — Казахстан и Урал",
    530: "🌄 GMT+5:30 — Индийский рассвет и чай с молоком",
    600: "🏡 GMT+6 — Омск и Бишкек",
    700: "🛤 GMT+7 — Красноярск и Новосибирск",
    800: "🌅 GMT+8 — Азия не спит — и я тоже",
    900: "🌅 GMT+9 — Якутск и Япония - в одном ритме",
    1000: "🌊 GMT+10 — Сидней, свежий воздух и продуктивность с утра",
    1100: "🌁 GMT+11 — Магадан - продуктивность весь день",
    1200: "GMT+12"
}











def calculate_timezone(user_time: datetime.datetime, current_utc_time: datetime.datetime | None = None):
    current_utc_time = current_utc_time or datetime.datetime.now(datetime.timezone.utc)

    delta = datetime.datetime.combine(datetime.date.today(), user_time.time()) - datetime.datetime.combine(datetime.date.today(), current_utc_time.time())

    delta = datetime.timedelta(seconds=round(delta.seconds / 1800) * 1800, days=delta.days)

    hours = round((delta.seconds + 24*3600*delta.days) // 3600) % 24
    minutes = round((delta.seconds + 24*3600*delta.days) // 60) % 60
    if hours > 12:
        hours = hours - 24
    print(hours, minutes, delta)
    return timezones_dict.get(hours * 100 + minutes), datetime.timedelta(hours=hours, minutes=minutes)
