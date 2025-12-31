import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory.buffer import ConversationBufferMemory
from langchain_core.runnables import RunnablePassthrough

# -------------------------------
# UID-based memory store
# -------------------------------
USER_MEMORY = {}

def get_memory(uid: str):
    if uid not in USER_MEMORY:
        USER_MEMORY[uid] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    return USER_MEMORY[uid]


# -------------------------------
# Gemini LLM
# -------------------------------
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.3
)

# -------------------------------
# Prompt
# -------------------------------
PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an AI Assistant for SVVCMS.

Rules:
- Answer ONLY from MCP data
- No hallucination
- Clear bullet points
- Remember previous context for this UID
"""
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])


def run_langchain(uid: str, mcp_data: str, user_question: str):
    memory = get_memory(uid)

    chain = (
            RunnablePassthrough.assign(
                chat_history=lambda _: memory.chat_memory.messages
            )
            | PROMPT
            | llm
    )

    response = chain.invoke({
        "input": f"""
MCP RESPONSE:
{mcp_data}

USER QUESTION:
{user_question}
"""
    })

    # Save AI response to memory
    memory.chat_memory.add_user_message(user_question)
    memory.chat_memory.add_ai_message(response.content)

    return response.content
