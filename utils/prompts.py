
TEXT_CHECK_PROMPT = """Analyze the following text: "{text}"

Based on the content and sentiment of the text, determine if it should be directed to a psychologist bot for sensitive, emotional, or mental health-related topics, or to a regular chatbot for general inquiries, factual questions, or casual conversation.

Respond with only "true" if the text should be sent to a psychologist bot.
Respond with only "false" if the text should be sent to a regular chatbot."""



IMAGE_CHECK_PROMPT = """Analyze the image.

Based on the visual content, depicted emotions, subject matter, and overall sentiment conveyed by the image, determine if it should be directed to a psychologist bot due to potentially sensitive, emotionally charged, distressing, or mental health-related themes. Otherwise, assume it can be handled by a regular chatbot for general image interpretation, object recognition, or casual content.

Respond with only "true" if the image should be sent to a psychologist bot.
Respond with only "false" if the image should be sent to a regular chatbot."""



DOCUMENT_CHECK_PROMPT = """Analyze the content of the document.

Based on the text, themes, subject matter, tone, and any explicit or implicit indications of emotional distress, mental health concerns, personal struggles, trauma, or other psychologically sensitive information contained within the document, determine if it should be directed to a psychologist bot. Otherwise, assume it can be handled by a regular chatbot for general information extraction, summarization, or topic analysis.

Respond with only "true" if the document should be sent to a psychologist bot.
Respond with only "false" if the document should be sent to a regular chatbot."""


RECOMMENDATION_PROMPT = """Основываясь на всех проблемах пользователя, дай строго один самый важный совет, который поможет ему решить проблему.
Действуй как психолог. Опиши всё подробно. Не задавай вопросов, пользователь не сможет ответить. Рекомендация должна быть готовой, как домашнее задание."""


MENTAL_DATA_PROVIDER_PROMPT = """Analyze all information about user. Based on it, act as the psychotherapist and write a complete, full user description.

This description should be useful for the psychologist to know all the information and help the user.

It should contain data about all user's mental problems, his therapy and previous consultations.

Provide structured output - each paragraph has to contain problem title and its description. 

Never drop any data - your output has to contain all current information plus new from dialog context.

Don't ask anything. I can't answer you. Just write all as possible."""

