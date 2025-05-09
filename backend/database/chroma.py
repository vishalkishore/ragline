import chromadb
from chromadb.config import Settings as ChromaSettings

from core.config import settings


class ChromaDB:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialise()
        return cls._instance

    def _initialise(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=ChromaSettings(),
        )

    def get_collection(self, collection_name: str):
        try:
            return self.client.get_or_create_collection(name=collection_name)
        except ValueError:
            return self.client.create_collection(name=collection_name)

    def get_collections(self):
        return self.client.list_collections()

    def delete_collection(self, collection_name: str):
        try:
            self.client.delete_collection(name=collection_name)
        except ValueError:
            pass
