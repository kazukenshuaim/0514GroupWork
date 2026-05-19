import json
import os

DATA_FILE_PATH = "data/inquiries.json"

def read_inquiries():
    if not os.path.exists(DATA_FILE_PATH):
        return []
    try:
        with open(DATA_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def write_inquiries(data):
    os.makedirs(os.path.dirname(DATA_FILE_PATH), exist_ok=True)
    with open(DATA_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)