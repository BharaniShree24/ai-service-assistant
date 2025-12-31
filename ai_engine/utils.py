import re

UID_PATTERN = re.compile(r"\bsvvcms\d+\b", re.IGNORECASE)

def extract_uid(text: str):
    match = UID_PATTERN.search(text)
    if match:
        return match.group(0)
    return None
