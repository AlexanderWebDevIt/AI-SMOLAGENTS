"""
Скрипт очистки загрязнённой памяти агента.

Удаляет:
1. Команды/задачи из cross_session_memory (оставляет только факты)
2. RAG-чанки conversation из чужих сессий (чтобы агент не выполнял команды из прошлых сессий)

Использование:
    python -m scripts.clean_memory        # очистить всё
    python -m scripts.clean_memory --dry-run  # показать что будет удалено, не удалять
"""

import os
import sys
import argparse

_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND_ROOT)

from app.memory.store import MemoryStore
from app.rag.engine import get_rag_engine

COMMAND_KEYWORDS = [
    "создай", "создать", "поменяй", "поменять", "измени", "изменить",
    "напиши", "написать", "сделай", "сделать", "выполни", "выполнить",
    "добавь", "добавить", "удали", "удалить", "исправь", "исправить",
    "загрузи", "загрузить", "скачай", "скачать", "прочитай", "прочитать",
    "открой", "открыть", "запусти", "запустить", "установи", "установить",
    "вопрос/задача", "task", "команда",
]


def clean_cross_session_memory(memory: MemoryStore, dry_run: bool = False) -> int:
    """Удаляет команды/задачи из cross_session_memory."""
    # Получаем напрямую через SQL
    conn = memory.conn
    cur = conn.execute("SELECT id, session_id, content FROM cross_session_memory")
    rows = cur.fetchall()

    removed = 0
    for row in rows:
        mem_id, session_id, content = row
        content_lower = content.lower()
        if any(kw in content_lower for kw in COMMAND_KEYWORDS):
            if dry_run:
                print(f"  [DRY] Удалил бы: {session_id}: {content[:80]}...")
            else:
                conn.execute("DELETE FROM cross_session_memory WHERE id = ?", (mem_id,))
                print(f"  [OK] Удалён: {session_id}: {content[:80]}...")
            removed += 1

    if not dry_run:
        conn.commit()
    return removed


def clean_rag_conversations(rag, keep_session_id: str = None, dry_run: bool = False) -> int:
    """Удаляет RAG-чанки conversation из сессий, кроме текущей (если указана)."""
    if not rag.available:
        print("  [SKIP] RAG не доступен")
        return 0

    try:
        client = rag.persistent_client
        collection = client.get_collection(name=rag_collection_name(rag))
        data = collection.get(include=["metadatas"])
        ids = data.get("ids") or []
        metadatas = data.get("metadatas") or []

        to_delete = []
        for doc_id, meta in zip(ids, metadatas):
            if meta.get("source") == "conversation":
                if keep_session_id and meta.get("session_id") != keep_session_id:
                    to_delete.append(doc_id)
                elif not keep_session_id:
                    to_delete.append(doc_id)

        if dry_run:
            print(f"  [DRY] Удалил бы {len(to_delete)} conversation-чанков")
        elif to_delete:
            collection.delete(ids=to_delete)
            print(f"  [OK] Удалено {len(to_delete)} conversation-чанков")
        return len(to_delete)
    except Exception as e:
        print(f"  [ERROR] Ошибка очистки RAG: {e}")
        return 0


def rag_collection_name(rag) -> str:
    """Определяет имя коллекции из метаданных."""
    try:
        return list(rag.persistent_client.get_collection().__dict__.keys())[0] if False else "assistant_main"
    except Exception:
        return "assistant_main"


def main():
    parser = argparse.ArgumentParser(description="Очистка памяти агента")
    parser.add_argument("--dry-run", action="store_true", help="Показать что будет удалено, не удалять")
    parser.add_argument("--keep-session", default=None, help="Сохранить conversation-чанки этой сессии")
    args = parser.parse_args()

    print("=" * 60)
    print("Очистка памяти агента")
    if args.dry_run:
        print("РЕЖИМ: DRY-RUN (ничего не удаляется)")
    print("=" * 60)

    # 1. Очистка cross_session_memory
    print("\n[1/2] Очистка cross_session_memory...")
    memory = MemoryStore()
    removed_cross = clean_cross_session_memory(memory, args.dry_run)
    print(f"  Удалено команд/задач: {removed_cross}")

    # 2. Очистка RAG conversation
    print("\n[2/2] Очистка RAG conversation-чанков...")
    rag = get_rag_engine(collection_name="assistant_main")
    removed_rag = clean_rag_conversations(rag, args.keep_session, args.dry_run)
    print(f"  Удалено conversation-чанков: {removed_rag}")

    print("\n" + "=" * 60)
    print(f"Готово! Очищено: {removed_cross + removed_rag}")
    print("=" * 60)


if __name__ == "__main__":
    main()