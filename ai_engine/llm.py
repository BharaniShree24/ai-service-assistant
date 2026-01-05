# llm.py
import os
from langchain_google_genai import ChatGoogleGenerativeAI

general_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
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
