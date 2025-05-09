import os
import uuid
from datetime import datetime

from core.config import settings
from database.chroma import ChromaDB
from document.models import Document, DocumentMetadata


class DocumentRepository:
    def __init__(self):
        self.chroma_db = ChromaDB()
        self._ensure_upload_dir()

    def _ensure_upload_dir(self):
        os.makedirs(settings.upload_dir, exist_ok=True)

    def save_file(self, file, filename=None):
        if filename is None:
            filename = file.filename

        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(settings.upload_dir, unique_filename)

        with open(filepath, "wb") as buffer:
            buffer.write(file.file.read())

        return filepath, unique_filename

    def create_document(self, metadata: DocumentMetadata) -> Document:
        document_id = str(uuid.uuid4())
        collection_name = f"doc_{document_id}"

        self.chroma_db.get_collection(collection_name)

        return Document(
            id=document_id, metadata=metadata, collection_name=collection_name
        )

    def get_document_by_id(self, document_id: str) -> Document | None:
        collection_name = f"doc_{document_id}"
        collections = self.chroma_db.get_collections()

        if any(c.name == collection_name for c in collections):
            return Document(
                id=document_id,
                metadata=DocumentMetadata(
                    filename=f"document_{document_id}.pdf",
                    upload_time=datetime.now(),
                ),
                collection_name=collection_name,
            )
        return None

    def get_all_documents(self) -> list[Document]:
        collections = self.chroma_db.get_collections()
        docs = []

        for coll in collections:
            if coll.name.startswith("doc_"):
                doc_id = coll.name[4:]
                docs.append(
                    Document(
                        id=doc_id,
                        metadata=DocumentMetadata(
                            filename=f"document_{doc_id}.pdf",
                            upload_time=datetime.now(),
                        ),
                        collection_name=coll.name,
                    )
                )

        return docs
