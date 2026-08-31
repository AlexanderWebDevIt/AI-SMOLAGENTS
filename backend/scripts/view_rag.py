"""
Скрипт просмотра содержимого RAG-базы знаний.

Использование:
    python -m scripts.view_rag              # список всех документов
    python -m scripts.view_rag --search "text"  # поиск по содержимому
    python -m scripts.view_rag --collection имя  # другая коллекция
"""

import os
import sys
import argparse

_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND_ROOT)

from app.rag.engine import get_rag_engine


def main():
    parser = argparse.ArgumentParser(description="Просмотр RAG-базы знаний")
    parser.add_argument("--collection", default="assistant_main", help="Имя RAG-коллекции")
    parser.add_argument("--search", default="", help="Поисковый запрос")
    parser.add_argument("--k", type=int, default=10, help="Количество результатов")
    args = parser.parse_args()

    rag = get_rag_engine(collection_name=args.collection)
    if not rag.available:
        print("[ERROR] RAG-движок недоступен.")
        sys.exit(1)

    try:
        client = rag.persistent_client
        collection = client.get_collection(name=args.collection)
        data = collection.get(include=["documents", "metadatas"])
        docs = data.get("documents") or []
        metadatas = data.get("metadatas") or []
        ids = data.get("ids") or []

        print("=" * 70)
        print(f"Коллекция: {args.collection}")
        print(f"Всего документов: {len(docs)}")
        print("=" * 70)

        if args.search:
            print(f"\nПоиск: '{args.search}' (k={args.k})\n")
            results = rag.search(args.search, k=args.k)
            for i, r in enumerate(results, 1):
                src = r.metadata.get("source", "?")
                fname = r.metadata.get("filename", r.metadata.get("topic", r.metadata.get("library", "?")))
                print(f"{i}. [{src}] {fname}")
                print(f"   {r.page_content[:150]}...")
                print()
        else:
            for i, (doc_id, doc, meta) in enumerate(zip(ids, docs, metadatas), 1):
                src = meta.get("source", "?")
                fname = meta.get("filename", meta.get("topic", meta.get("library", meta.get("url", "?"))))
                print(f"{i}. ID: {doc_id}")
                print(f"   Источник: {src} | Файл/тема: {fname}")
                print(f"   Содержимое: {doc[:100]}...")
                print()

    except Exception as e:
        print(f"[ERROR] Ошибка чтения коллекции: {e}")
        # Показываем все коллекции
        try:
            print("\nДоступные коллекции:")
            for col in client.list_collections():
                print(f"  - {col.name}")
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()