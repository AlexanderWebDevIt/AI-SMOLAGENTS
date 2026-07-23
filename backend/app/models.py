import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = os.path.join(os.getcwd(), "data")
ACTIVE_MODEL_FILE = os.path.join(DATA_DIR, "active-model.json")


def get_lm_studio_url() -> str:
    return os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1")


def get_api_key() -> str:
    return os.getenv("OPENAI_API_KEY", "lm-studio")


def get_models() -> list:
    base_url = get_lm_studio_url()
    api_key = get_api_key()

    try:
        response = requests.get(
            f"{base_url}/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        models = []
        for m in data.get("data", []):
            model_id = m.get("id", "")
            is_embedding = "embed" in model_id.lower()
            models.append({
                "id": model_id,
                "name": model_id.split("/")[-1] if "/" in model_id else model_id,
                "type": "embedding" if is_embedding else "chat",
                "owned_by": m.get("owned_by", "unknown"),
            })
        return models
    except Exception as e:
        print(f"[Models] Ошибка получения списка моделей: {e}")
        return []


def get_chat_models() -> list:
    return [m for m in get_models() if m["type"] == "chat"]


def get_active_model() -> str:
    if os.path.exists(ACTIVE_MODEL_FILE):
        try:
            with open(ACTIVE_MODEL_FILE, "r") as f:
                data = json.load(f)
                return data.get("model_id", "")
        except Exception:
            pass

    models = get_chat_models()
    if models:
        return models[0]["id"]
    return "local-model"


def set_active_model(model_id: str):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ACTIVE_MODEL_FILE, "w") as f:
        json.dump({"model_id": model_id}, f, indent=2)


def test_model(model_id: str) -> dict:
    base_url = get_lm_studio_url()
    api_key = get_api_key()

    try:
        from openai import OpenAI
        client = OpenAI(base_url=base_url, api_key=api_key)
        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": "Привет"}],
            max_tokens=50,
        )
        reply = response.choices[0].message.content
        return {"status": "ok", "reply": reply}
    except Exception as e:
        return {"status": "error", "error": str(e)}
