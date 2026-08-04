import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
ACTIVE_MODEL_FILE = os.path.join(DATA_DIR, "active-model.json")
PROVIDERS_FILE = os.path.join(DATA_DIR, "providers.json")

# Model cache
_model_cache = {"data": None, "timestamp": 0}
MODEL_CACHE_TTL = 10  # seconds

DEFAULT_PROVIDERS = {
    "lmstudio": {
        "name": "LM Studio",
        "base_url": "http://localhost:1234/v1",
        "api_key": "lm-studio",
        "type": "local"
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "api_key": "",
        "type": "cloud"
    },
    "ollama": {
        "name": "Ollama",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
        "type": "local"
    },
    "together": {
        "name": "Together AI",
        "base_url": "https://api.together.xyz/v1",
        "api_key": "",
        "type": "cloud"
    },
    "openrouter": {
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": "",
        "type": "cloud"
    }
}


def get_lm_studio_url() -> str:
    return os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1")


def get_api_key() -> str:
    return os.getenv("OPENAI_API_KEY", "lm-studio")


def get_models(force_refresh: bool = False) -> list:
    global _model_cache
    now = time.time()
    if not force_refresh and _model_cache["data"] and (now - _model_cache["timestamp"]) < MODEL_CACHE_TTL:
        return _model_cache["data"]

    config = get_provider_config()
    base_url = config.get("base_url", "http://localhost:1234/v1")
    api_key = config.get("api_key", "lm-studio")

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
        _model_cache = {"data": models, "timestamp": now}
        return models
    except Exception as e:
        print(f"[Models] Ошибка получения списка моделей: {e}")
        if _model_cache["data"]:
            print(f"[Models] Возвращаю кэшированные данные (от {time.time() - _model_cache['timestamp']:.0f}s назад)")
            return _model_cache["data"]
        return []


def get_chat_models() -> list:
    return [m for m in get_models() if m["type"] == "chat"]


def get_active_model() -> str:
    """Return saved model id only — never auto-pick from provider."""
    if os.path.exists(ACTIVE_MODEL_FILE):
        try:
            with open(ACTIVE_MODEL_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("model_id", "")
        except Exception:
            pass
    return ""


def set_active_model(model_id: str):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ACTIVE_MODEL_FILE, "w", encoding="utf-8") as f:
        json.dump({"model_id": model_id, "verified": True}, f, indent=2)


def is_model_available(model_id: str) -> bool:
    if not model_id:
        return False
    return any(m["id"] == model_id for m in get_chat_models())


def validate_active_model() -> dict:
    model_id = get_active_model()
    if not model_id:
        return {"status": "none", "model_id": "", "message": "Модель не выбрана"}
    if is_model_available(model_id):
        return {"status": "ok", "model_id": model_id, "message": "Модель доступна"}
    return {
        "status": "unavailable",
        "model_id": model_id,
        "message": f"Модель '{model_id}' недоступна у текущего провайдера",
    }


def test_model(model_id: str) -> dict:
    config = get_provider_config()
    base_url = config.get("base_url", get_lm_studio_url())
    api_key = config.get("api_key", get_api_key())

    try:
        from openai import OpenAI
        client = OpenAI(base_url=base_url, api_key=api_key)
        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=10,
        )
        reply = response.choices[0].message.content
        return {"status": "ok", "reply": reply}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def get_providers() -> dict:
    if os.path.exists(PROVIDERS_FILE):
        try:
            with open(PROVIDERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_PROVIDERS


def save_providers(providers: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PROVIDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(providers, f, indent=2, ensure_ascii=False)


def set_provider(provider_id: str, config: dict):
    providers = get_providers()
    providers[provider_id] = config
    save_providers(providers)

    os.environ["OPENAI_BASE_URL"] = config.get("base_url", "")
    os.environ["OPENAI_API_KEY"] = config.get("api_key", "")


def get_provider_config(provider_id: str = None) -> dict:
    providers = get_providers()
    if provider_id:
        return providers.get(provider_id, {})

    active_file = os.path.join(DATA_DIR, "active-provider.json")
    if os.path.exists(active_file):
        with open(active_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return providers.get(data.get("provider_id", "lmstudio"), {})

    return providers.get("lmstudio", {})


def set_active_provider(provider_id: str):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, "active-provider.json"), "w", encoding="utf-8") as f:
        json.dump({"provider_id": provider_id}, f)

    config = get_provider_config(provider_id)
    if config:
        os.environ["OPENAI_BASE_URL"] = config.get("base_url", "")
        os.environ["OPENAI_API_KEY"] = config.get("api_key", "")
