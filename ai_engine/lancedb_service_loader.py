import json
import lancedb
import pandas as pd
from sentence_transformers import SentenceTransformer

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(BASE_DIR, "svvcms_services.json")
LANCE_DB_PATH = os.path.join(BASE_DIR, "lancedb_data")

with open(json_path, "r", encoding="utf-8") as f:
    services = json.load(f)["services"]


# Prepare embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")

texts = [s["name"] for s in services]
embeddings = model.encode(texts)

df = pd.DataFrame({
    "service_name": [s["name"] for s in services],
    "app_id": [s["app_id"] for s in services],
    "vector": embeddings.tolist()
})  

# Store in LanceDB
db = lancedb.connect(LANCE_DB_PATH)
db.create_table("svvcms_services", df, mode="overwrite")

print("✅ Services successfully stored in LanceDB")


#
# import lancedb
#
# db = lancedb.connect("lancedb_data")
# print(db.list_tables())
#
# table = db.open_table("svvcms_services")
# print(table.to_pandas().head())
#
# df = table.to_pandas()
# print("Total rows:", len(df))  # Check total number of services
# print(df[['service_name', 'app_id']])  # Print all services without vector column
#
# # Open PDF documents table
# if "pdf_documents" in [t.name for t in db.list_tables()]:
#     pdf_table = db.open_table("pdf_documents")
#     pdf_df = pdf_table.to_pandas()
#     print("\n--- PDF Chunks ---")
#     print(pdf_df.head())
#     print("Total PDF chunks:", len(pdf_df))
#     print(pdf_df[['text', 'source']])  # text chunks and PDF file source
# else:
#     print("❌ Table 'pdf_documents' does not exist")
#
#
