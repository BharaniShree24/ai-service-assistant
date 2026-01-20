# inspect_lancedb.py
import lancedb

# Connect to LanceDB folder
db = lancedb.connect("lancedb_data")

# Get table names as strings
tables = [t.name for t in db.list_tables()]
print("✅ Existing tables:", tables)

print("\n==============================")
for table_name in tables:
    print(f"Table: {table_name}")

    table = db.open_table(table_name)
    df = table.to_pandas()
    total_rows = len(df)
    print(f"Total rows: {total_rows}")

    # Show first 5 rows
    print("\n--- First 5 rows ---")
    print(df.head())

    # Show only relevant columns
    if table_name == "svvcms_services":
        print("\n--- Key columns ---")
        if all(col in df.columns for col in ["service_name", "app_id"]):
            print(df[["service_name", "app_id"]])
        else:
            print("❌ Expected columns not found in svvcms_services")
    elif table_name == "pdf_documents":
        print("\n--- Key columns ---")
        if all(col in df.columns for col in ["text", "source"]):
            print(df[["text", "source"]])
        else:
            print("❌ Expected columns not found in pdf_documents")

    print("\n==============================")

# Check if expected tables are missing
expected_tables = ["svvcms_services", "pdf_documents"]
for t in expected_tables:
    if t not in tables:
        print(f"❌ Table '{t}' does NOT exist. You can create it by storing data.")
