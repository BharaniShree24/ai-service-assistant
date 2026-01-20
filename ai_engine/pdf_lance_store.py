import os
import lancedb
import pandas as pd
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LANCE_DB_PATH = os.path.join(BASE_DIR, "lancedb_data")
TABLE_NAME = "pdf_documents"

model = SentenceTransformer("all-MiniLM-L6-v2")


def extract_text(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t + "\n"
    return text


def chunk_text(text, size=500, overlap=100):
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def store_pdf_to_lance(pdf_path):
    text = extract_text(pdf_path)
    chunks = chunk_text(text)

    if not chunks:
        return

    vectors = model.encode(chunks).tolist()

    df = pd.DataFrame({
        "text": chunks,
        "vector": vectors,
        "source": os.path.basename(pdf_path)
    })

    db = lancedb.connect(LANCE_DB_PATH)

    if TABLE_NAME not in db.list_tables():
        db.create_table(TABLE_NAME, df)
    else:
        db.open_table(TABLE_NAME).add(df)

    print(f"✅ Stored {len(chunks)} PDF chunks in LanceDB")
