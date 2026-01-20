import os
import re
import hashlib

from django.core.cache import cache
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory.buffer import ConversationBufferMemory
from langchain_core.runnables import RunnablePassthrough

import configparser
import os


config = configparser.ConfigParser()
config.read(os.path.join(os.getcwd(), 'config.ini'))

GEMINI_API_KEY = config['DEFAULT']['GEMINI_API_KEY']



# ==========================================================
# UID-based memory store (per service / per user)
# ==========================================================
USER_MEMORY = {}


def get_memory(uid: str) -> ConversationBufferMemory:
    """
    Returns conversation memory for a given UID.
    Creates new memory if not present.
    """
    if uid not in USER_MEMORY:
        USER_MEMORY[uid] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    return USER_MEMORY[uid]


# ==========================================================
# Utility functions
# ==========================================================
def normalize_text(text: str) -> str:
    """
    Normalize text for caching (lowercase, no symbols).
    """
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text.strip()


def get_cache_key(uid: str, question: str) -> str:
    """
    Generate cache key based on UID + normalized question.
    """
    normalized_question = normalize_text(question)
    hash_part = hashlib.md5(normalized_question.encode()).hexdigest()
    return f"ai_cache_{uid}_{hash_part}"


# ==========================================================
# Gemini LLM
# ==========================================================
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    gemini_api_key=str(GEMINI_API_KEY),
    temperature=0.3
)


# ==========================================================
# Prompt Template
# ==========================================================
PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an AI Assistant for SVVCMS.

Rules:
- If the user greets or makes small talk, reply politely.
- Use MCP data ONLY when the question is service-related.
- Do NOT repeat service details unless the user asks.
- Never hallucinate or assume missing data.
"""
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")
    ]
)


# ==========================================================
# Main LangChain Runner
# ==========================================================
def run_langchain(uid: str, mcp_data: str, user_question: str) -> str:
    """
    Runs LangChain with Gemini using:
    - UID-based memory
    - MCP data (when available)
    - Caching for repeated questions
    """

    # ----------------------------
    #1️⃣ Cache check
    # ----------------------------
    cache_key = get_cache_key(uid, user_question)
    cached_reply = cache.get(cache_key)
    if cached_reply:
        return cached_reply

    # ----------------------------
    # 2️⃣ Get memory
    # ----------------------------
    memory = get_memory(uid)

    # ----------------------------
    # 3️⃣ Build chain
    # ----------------------------
    chain = (
        RunnablePassthrough.assign(
            chat_history=lambda _: memory.chat_memory.messages
        )
        | PROMPT
        | llm
    )

    # ----------------------------
    # 4️⃣ Invoke Gemini
    # ----------------------------
    response = chain.invoke(
        {
            "input": f"""
You are answering ONLY based on the service information provided below.
Do NOT assume anything outside this information.

SERVICE INFORMATION:
{mcp_data}

USER QUESTION:
{user_question}
"""

        }
    )

    # ----------------------------
    # 5️⃣ Save to memory
    # ----------------------------
    memory.chat_memory.add_user_message(user_question)
    memory.chat_memory.add_ai_message(response.content)

    # ----------------------------
    # 6️⃣ Save to cache (15 min)
    # ----------------------------
    cache.set(cache_key, response.content, timeout=900)

    return response.content
