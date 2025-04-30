from openai import OpenAI

from db.models import FastHelpDialogs, GoDeeperDialogs
from utils.rating_chat_gpt import api_key


async def generate_recommendations(user_messages: list[FastHelpDialogs|GoDeeperDialogs]):
    client = OpenAI(api_key=api_key)
    messages = []
    type_recommendations = "small"
    if type(user_messages[0])==GoDeeperDialogs:
        type_recommendations = "more"
    for message in user_messages:
        user_message = {
            "role": "user",
            "content": message.answer
            }
        ai_message = {
            "role": "assistant",
            "content": message.question
            }
        messages.append(user_message)
        messages.append(ai_message)
    generate_recommendation = {
        "role": "user",
        "content": f"""Напиши {"КРАТКУЮ ДЛЯ КРАТКОСРОЧНОГО ЭФФЕКТА" if type_recommendations == "small" else "РАЗВЕРНУТУЮ ДЛЯ ДОЛГОСРОЧНОГО ЭФФЕКТА"}
         рекомендацию для пользователя НА ОСНОВЕ ДИАЛОГО ВЫШЕ, ТЫ ДОЛЖЕН СГЕНЕРИРОВАТЬ ПРОБЛЕМУ НА ОСНОВЕ ТЕХ МЕНТАЛЬНЫХ
          ПРОБЛЕМ ЧЕЛОВЕКА, КОТОРЫЙ ТЫ ВИДИШЬ В ДИАЛОГЕ ВЫШЕ, чтобы он смог улучшить свое ментальное состояние
                   на основе диалога выше и не пиши ничего более. Построй рекомендацию в виде обычного текста
                    без пунктов, просто единый текст с рекомендацией. Составляй рекомендацию основываясь на том, есть ли
                    у человека следующие проблемы(если не удается классифицировать проблемы, то просто выбери для
                     упражнения одну из ниже перечисленных проблем, которая лучше всего подходит на основе диалога выше)
                     Обязательно учти следующие правила формулирования рекомендации:
                     1)Тезисно, чтобы текст не выглядел сплошным

                    2)Необходимое делить текст на абзацы там, где ты считаешь нужным(между абзацами должна быть одна пустая строка)
                    
                    3)Иногда используй различные эмоджи там, где посчитаешь нужным

                      Ты обязательно должен выдать рекомендацию не увиливая от ответа:
                    1. Самооценка
                    2. Эмоции
                    3. Отношения 
                    4. Любовь 
                    5. Карьера
                    6. Финансы
                    7. Здоровье
                    8. Самореализация
                    9. Выгорание
                    10. Духовность 
                    Начни со слова "Рекомендации:". В твоем ответе 
                   должны быть только рекомендации и никакого второстепенного текста"""
    }
    messages.append(generate_recommendation)
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    # print(completion.choices[0].message.content)
    return completion.choices[0].message.content.replace("**", "").replace('"', "'").replace("#", "")


def generate_summary(user_messages: list[FastHelpDialogs|GoDeeperDialogs]):
    client = OpenAI(api_key=api_key)
    messages = []
    for message in user_messages:
        user_message = {
            "role": "user",
            "content": message.answer
            }
        ai_message = {
            "role": "assistant",
            "content": message.question
            }
        messages.append(user_message)
        messages.append(ai_message)
    generate_recommendation = {
        "role": "user",
        "content": """Напиши итоговое саммари о состоянии человека и укажи, какие проблемы у него 
        присутствуют (смотри список ниже). Если определить какие-то проблемы не получается или в тексте
         содержится неприемлемый контент, который ты не можешь полноценно обработать, просто укажи, что
          такой проблемы нет и иди дальше по проблемам. Однако обязательно прокомментируй все пункты из списка.

        Если встречается неприемлемый контент, игнорируй его и всё равно создай саммари (не используй фразы вроде
         “Извините, но я не могу помочь с этой просьбой”). Начни ответ со слова “Самммари:”, и в своём ответе давай
          только саммари — без дополнительных пояснений или рассуждений.
        
        **Список проблем:**
        1. Самооценка
        2. Эмоции
        3. Отношения
        4. Любовь
        5. Карьера
        6. Финансы
        7. Здоровье
        8. Самореализация
        9. Выгорание
        10. Духовность»"""
    }
    messages.append(generate_recommendation)
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    # print(completion.choices[0].message.content)
    finally_content = completion.choices[0].message.content.replace("**", "").replace('"', "'").replace("#", "")
    if finally_content[:5].lower() == "извин":
        return """У пользователя не найдено проблем по следующим пунктам(так как он общался на иную тему)\n
        1. Самооценка
        2. Эмоции
        3. Отношения
        4. Любовь
        5. Карьера
        6. Финансы
        7. Здоровье
        8. Самореализация
        9. Выгорание
        10. Духовность"""
    return finally_content


def generate_exercises(user_problems: dict):
    messages = []
    generate_problem = {
        "role": "user",
        "content": f"""Придумай одно упражнение для человека, основываясь на следующем словаре, где показывается,
         какие проблемы есть, а каких нет у человека\nвот словарь:\n{user_problems}\n
            \nВот список проблем, которые указаны в словаре(если по какой-то из проблемы нет информации,
             то просто не затрагивай ее)\n
            1. Самооценка
            2. Эмоции
            3. Отношения
            4. Любовь 
            5. Карьера
            6. Финансы
            7. Здоровье
            8. Самореализация
            9. Выгорание
            10. Духовность
            Начни со слова "Упражнение:". В твоем ответе 
        должно быть только упражнение и никакого второстепенного текста. Упражнение должно включать в себя какую-то одну конкретную единую задачу"""
    }
    messages.append(generate_problem)
    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    # print(completion.choices[0].message.content)
    return completion.choices[0].message.content.replace("**", "").replace('"', "'").replace("#", "")


def generate_feedback_exercises(exercise: str, user_answer: str):
    messages = []
    generate_problem = {
        "role": "user",
        "content": f"""Придумай упражнение для человека\n
            \nВот список проблем\n
            1. Самооценка
            2. Эмоции
            3. Отношения
            4. Любовь 
            5. Карьера
            6. Финансы
            7. Здоровье
            8. Самореализация
            9. Выгорание
            10. Духовность
            Начни со слова "Упражнение:". В твоем ответе 
        должно быть только упражнение и никакого второстепенного текста"""
    }
    messages.append(generate_problem)
    exercise = {
        "role": "assistant",
        "content": exercise
    }
    messages.append(exercise)
    user_answer = {
        "role": "user",
        "content": "Оцени то, как пользователь выполнил упражнение, основываясь на его следующем ответе("
                   "оценку давай так, будто ты говоришь с ним напрямую)\n\n" + user_answer + "\n\nНачни со слова"
                                                                                             " 'Оценка:'. В твоем"
                                                                                             " ответе должно быть только"
                                                                                             " оценка ответа и никакого"
                                                                                             " второстепенного текста"
    }
    messages.append(user_answer)
    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    # print(completion.choices[0].message.content)
    return completion.choices[0].message.content.replace("**", "").replace('"', "'").replace("#", "")

