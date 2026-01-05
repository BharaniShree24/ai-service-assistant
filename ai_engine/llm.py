# llm.py
import os
from langchain_google_genai import ChatGoogleGenerativeAI

import configparser
import os


config = configparser.ConfigParser()
config.read(os.path.join(os.getcwd(), 'config.ini'))

GEMINI_API_KEY = config['DEFAULT']['GEMINI_API_KEY']


general_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=str(GEMINI_API_KEY),
    temperature=0.7
)


def general_llm_call(user_input: str) -> str:
    response = general_llm.invoke(
        f"""
You are a friendly AI assistant.
Respond naturally and politely.

User message:
{user_input}
"""
    )
    return response.content
