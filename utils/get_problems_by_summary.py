import asyncio
import json
import traceback
from os import getenv

from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

from settings import mental_problems_function


load_dotenv(find_dotenv("../.env"))
api_key = getenv("GPT_TOKEN")

def get_problems_by_summary_user(summary: str):
    try:
        client = OpenAI(api_key=api_key)

        tools = [mental_problems_function]


        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": summary}],
            tools=tools,
            timeout=15
        )
        # print("\n" * 4)
        # print(completion.choices[0].message)
        # print("\n" * 4)
        # print(completion)
        json_str = completion.choices[0].message.tool_calls[0].function.arguments
        data = json.loads(json_str)
        print(data)
        problems = ['self_esteem', 'emotions', 'relationships', 'love', 'career', 'finances', 'health',
                    'self_actualization', "burnout", "spirituality"]
        list_data = list(data.keys())
        for problem in problems:
            if problem not in data:
                data[problem] = True
        if len(data.keys()) < 10:
            return {problem: True for problem in problems}
        return data

    except Exception as e:
        full_error = traceback.format_exc()
        print(f"Произошла ошибка или истёк лимит ожидания: {full_error}")
        # Возвращаем значение по умолчанию, если произошёл timeout или другая ошибка
        return {problem: True for problem in [
            'self_esteem', 'emotions', 'relationships', 'love', 'career',
            'finances', 'health', 'self_actualization', 'burnout', 'spirituality'
        ]}