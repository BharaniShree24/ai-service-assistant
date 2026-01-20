import lancedb
from sentence_transformers import SentenceTransformer
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LANCE_DB_PATH = os.path.join(BASE_DIR, "lancedb_data")

db = lancedb.connect(LANCE_DB_PATH)
table = db.open_table("svvcms_services")

model = SentenceTransformer("all-MiniLM-L6-v2")


def resolve_service_from_text(user_text: str):
    query_vector = model.encode(user_text)

    results = (
        table.search(
            query_vector,
            vector_column_name="vector"
        )
        .limit(1)
        .to_pandas()
    )

    if results.empty:
        return None

    row = results.iloc[0]

    return {
        "uid": row["app_id"],
        "service_name": row["service_name"]
    }


# print("LANCE_DB_PATH:", LANCE_DB_PATH)
# print("List of Tables:", db.list_tables())

