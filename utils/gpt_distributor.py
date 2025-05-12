from openai import OpenAI

from settings import openai_api_key


class UserRequestHandler:
    def __init__(self):
        self.openAI_client = OpenAI(api_key=openai_api_key)


    def handle(self, user_id: int, text: str, image_bytes = None, ):
        pass

    def is_request_mental(self):
        pass
