import os
from langchain_huggingface import HuggingFaceEmbeddings
import chromadb
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

class RAGEngine:
    def __init__(self, collection_name: str = "knowledge"):
        self.available = False
        try:
            # Мы переходим на локальные эмбеддинги прямо в Python
            # Модель 'all-MiniLM-L6-v2' — это стандарт индустрии для быстрых и точных локальных RAG
            self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

            db_path = os.path.join(os.getcwd(), "data", "chroma_db")
            os.makedirs(db_path, exist_ok=True)

            self.persistent_client = chromadb.PersistentClient(path=db_path)
            self.vector_store = Chroma(
                client=self.persistent_client,
                collection_name=collection_name,
                embedding_function=self.embeddings,
            )
            self.available = True
            print("[RAG] Система RAG успешно инициализирована (Local Embeddings).")
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
            # Поиск теперь происходит локально через наши HuggingFace эмбеддинги
            return self.vector_store.similarity_search(query, k=k)
        except Exception as e:
            print(f"[RAG] Ошибка поиска: {e}")
            return []
