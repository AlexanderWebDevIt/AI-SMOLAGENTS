import os
import threading
from langchain_huggingface import HuggingFaceEmbeddings
import chromadb
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

_instances = {}
_lock = threading.Lock()


def get_rag_engine(collection_name: str = "knowledge") -> "RAGEngine":
    """Get or create a RAGEngine singleton per collection name."""
    with _lock:
        if collection_name not in _instances:
            _instances[collection_name] = RAGEngine(collection_name)
        return _instances[collection_name]


def prewarm_rag():
    """Pre-initialize the default RAG engine. Call at server startup to avoid
    slow first request (HuggingFaceEmbeddings model loading takes 10-30s)."""
    try:
        get_rag_engine("assistant_main")
        print("[RAG] Pre-warmed RAG engine")
    except Exception as e:
        print(f"[RAG] Pre-warm failed (will retry on first request): {e}")


class RAGEngine:
    def __init__(self, collection_name: str = "knowledge"):
        self.available = False
        try:
            self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

            _backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(_backend_root, "data", "chroma_db")
            os.makedirs(db_path, exist_ok=True)

            self.persistent_client = chromadb.PersistentClient(path=db_path)
            self.vector_store = Chroma(
                client=self.persistent_client,
                collection_name=collection_name,
                embedding_function=self.embeddings,
            )
            self.available = True
            print(f"[RAG] Система RAG инициализирована (коллекция: {collection_name}).")
        except Exception as e:
            print(f"[RAG] Ошибка инициализации: {e}")
            self.vector_store = None

    def add_document(self, text: str, metadata: dict = None) -> int:
        if not self.available or not text:
            return 0
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )
        chunks = splitter.split_text(text)
        if chunks:
            self.vector_store.add_texts(chunks, metadatas=[metadata or {}] * len(chunks))
        return len(chunks)

    def search(self, query: str, k: int = 5):
        if not self.available or self.vector_store is None:
            return []
        
        try:
            return self.vector_store.similarity_search(query, k=k)
        except Exception as e:
            print(f"[RAG] Ошибка поиска: {e}")
            return []
