"""File attachment storage for chat."""
import os
import uuid
import json
import base64
from datetime import datetime

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS_DIR = os.path.join(_BACKEND_DIR, "data", "uploads")

# Разрешённые типы файлов
ALLOWED_EXTENSIONS = {
    # Изображения
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg",
    # Текстовые документы
    ".txt", ".md", ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".csv",
    # Код
    ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".html", ".css", ".yaml", ".yml", ".toml",
    ".sh", ".bat", ".ps1",
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

_image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}
_text_extensions = {".txt", ".md", ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".html", ".css", ".yaml", ".yml", ".toml", ".sh", ".bat", ".ps1", ".csv"}


def get_upload_dir() -> str:
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    return UPLOADS_DIR


def save_upload(content: bytes, filename: str) -> dict:
    """Save an uploaded file, return metadata dict."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Недопустимый тип файла: " + (ext or "(без расширения)"))
    if len(content) > MAX_FILE_SIZE:
        raise ValueError("Файл слишком большой (макс. 20 MB)")

    file_id = str(uuid.uuid4())
    safe_name = os.path.basename(filename)
    save_path = os.path.join(get_upload_dir(), file_id + ext)

    with open(save_path, "wb") as f:
        f.write(content)

    # Sidecar .meta — сохраняем оригинальное имя файла
    meta_path = save_path + ".meta"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"filename": safe_name}, f, ensure_ascii=False)

    file_type = "image" if ext in _image_extensions else "text" if ext in _text_extensions else "document"
    return {
        "id": file_id,
        "filename": safe_name,
        "type": file_type,
        "ext": ext,
        "size": len(content),
        "url": "/api/files/" + file_id,
        "created_at": datetime.now().isoformat(),
    }


def get_upload_path(file_id: str) -> str:
    """Find file by ID (scan uploads dir)."""
    uploads = get_upload_dir()
    for fname in os.listdir(uploads):
        if fname.startswith(file_id + "."):
            return os.path.join(uploads, fname)
    return None


def get_file_metadata(file_id: str) -> dict:
    """Get metadata by reading the actual file."""
    path = get_upload_path(file_id)
    if not path:
        return None
    ext = os.path.splitext(path)[1].lower()
    meta_path = path + ".meta"
    filename = os.path.basename(path)
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                filename = json.load(f).get("filename", filename)
        except Exception:
            pass
    size = os.path.getsize(path)
    file_type = "image" if ext in _image_extensions else "text" if ext in _text_extensions else "document"
    return {
        "id": file_id,
        "filename": filename,
        "type": file_type,
        "ext": ext,
        "size": size,
        "url": "/api/files/" + file_id,
    }


def delete_upload(file_id: str):
    """Delete an uploaded file and its metadata."""
    path = get_upload_path(file_id)
    if path:
        try:
            os.unlink(path)
        except Exception:
            pass
        meta = path + ".meta"
        if os.path.exists(meta):
            try:
                os.unlink(meta)
            except Exception:
                pass


def read_text_file(file_id: str, max_chars: int = 5000) -> str:
    """Read text content of a file for inclusion in prompt."""
    path = get_upload_path(file_id)
    if not path:
        return None
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        if len(text) > max_chars:
            text = text[:max_chars] + "\n... (обрезано)"
        return text
    except Exception:
        return None


def read_image_base64(file_id: str) -> str:
    """Read image file as base64 data URL for vision models."""
    path = get_upload_path(file_id)
    if not path:
        return None
    ext = os.path.splitext(path)[1].lower()
    if ext not in _image_extensions:
        return None
    try:
        with open(path, "rb") as f:
            data = f.read()
        mime = {
            ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
            ".svg": "image/svg+xml",
        }.get(ext, "application/octet-stream")
        return "data:" + mime + ";base64," + base64.b64encode(data).decode("utf-8")
    except Exception:
        return None


def is_image(file_id: str) -> bool:
    path = get_upload_path(file_id)
    if not path:
        return False
    ext = os.path.splitext(path)[1].lower()
    return ext in _image_extensions