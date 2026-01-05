import json
import re

JSON_PATH = "ai_engine/svvcms_services.json"


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return text.strip()


def load_services():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["services"]


def resolve_uid_from_text(user_text: str):
    user_text = normalize(user_text)
    services = load_services()

    for service in services:
        for keyword in service["keywords"]:
            if normalize(keyword) in user_text:
                return {
                    "uid": service["app_id"],
                    "service_name": service["name"]
                }

    return None
