
import hashlib
import json
from pathlib import Path

CACHE_FILE = Path(__file__).resolve().parent / "response_cache.json"


def _load_cache() -> dict:
    if not CACHE_FILE.exists():
        return {}

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


def get_cache_key(task: str, model: str) -> str:
    content = f"{model}:{task.strip()}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def get_cached_response(task: str, model: str):
    cache = _load_cache()
    key = get_cache_key(task, model)
    return cache.get(key)


def save_cached_response(task: str, model: str, answer: str) -> None:
    cache = _load_cache()
    key = get_cache_key(task, model)
    cache[key] = answer

    with open(CACHE_FILE, "w", encoding="utf-8") as file:
        json.dump(cache, file, indent=2, ensure_ascii=False)
