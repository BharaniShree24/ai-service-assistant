import os
import pandas as pd
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from google import genai
import configparser
from typing import List

# ---------- CONFIG.INI LOAD ----------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config.ini")

config = configparser.ConfigParser()
config.read(CONFIG_PATH)

GEMINI_API_KEY = config.get("DEFAULT", "GEMINI_API_KEY", fallback=None)
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in config.ini")

# ---------- GEMINI CLIENT ----------
client = genai.Client(api_key=GEMINI_API_KEY)

# ---------- EMBEDDING MODEL ----------
model_embed = SentenceTransformer("all-MiniLM-L6-v2")


# ---------- GEMINI CALL ----------
def ask_gemini(prompt: str) -> str:
    """Send a prompt to Gemini AI and return the response text."""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text


# ---------- PDF TEXT EXTRACTION ----------
def extract_text(pdf_path: str) -> str:
    """Extract text from a PDF file."""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text.strip()


# ---------- TEXT CHUNKING ----------
def chunk_text(text: str, size: int = 500, overlap: int = 100) -> List[str]:
    """Split text into chunks for embedding."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


# ---------- ON-THE-FLY QUERY ----------
def query_uploaded_pdf(pdf_path: str, question: str, top_k: int = 3):
    text = extract_text(pdf_path)
    if not text:
        return None

    chunks = chunk_text(text)
    embeddings = model_embed.encode(chunks).tolist()

    q_embed = model_embed.encode(question).tolist()

    import numpy as np
    from numpy.linalg import norm

    def cosine_similarity(a, b):
        return np.dot(a, b) / (norm(a) * norm(b) + 1e-10)

    similarities = [cosine_similarity(q_embed, vec) for vec in embeddings]
    top_indices = sorted(range(len(similarities)), key=lambda i: similarities[i], reverse=True)[:top_k]

    context = "\n".join([chunks[i] for i in top_indices])

    prompt = f"""
You are a document assistant.
Answer ONLY from the context below.
If not available, say: Information not found in document.

Context:
{context}

Question:
{question}
"""

    answer = ask_gemini(prompt)

    if "Information not found in document" in answer:
        return None

    return answer

