import os

from fastapi import UploadFile

from document.models import DocumentMetadata, DocumentResponse
from document.repository import DocumentRepository
from pipeline.document_processor import DocumentProcessor


class DocumentService:
    def __init__(self):
        self.repository = DocumentRepository()
        self.processor = DocumentProcessor()

    async def upload_document(self, file: UploadFile) -> DocumentResponse:
        if not file.filename.lower().endswith(".pdf"):
            raise ValueError("Only PDF files are supported")

        filepath, unique_filename = self.repository.save_file(file)

        try:
            # collect metadata
            file_size = os.path.getsize(filepath)
            metadata = DocumentMetadata(
                filename=file.filename, file_size=file_size, document_type="pdf"
            )
            document = self.repository.create_document(metadata)
            chunks_count = self.processor.process_document(document, filepath)
            document.metadata.page_count = chunks_count

            return DocumentResponse(
                id=document.id,
                filename=file.filename,
                upload_time=document.metadata.upload_time,
                page_count=chunks_count,
                file_size=file_size,
            )
        except Exception:
            raise

    def get_document(self, document_id: str) -> DocumentResponse | None:

        document = self.repository.get_document_by_id(document_id)
        if not document:
            return None

        return DocumentResponse(
            id=document.id,
            filename=document.metadata.filename,
            upload_time=document.metadata.upload_time,
            page_count=document.metadata.page_count,
            file_size=document.metadata.file_size,
        )

    def get_all_documents(self) -> list[DocumentResponse]:
        documents = self.repository.get_all_documents()
        return [
            DocumentResponse(
                id=doc.id,
                filename=doc.metadata.filename,
                upload_time=doc.metadata.upload_time,
                page_count=doc.metadata.page_count,
                file_size=doc.metadata.file_size,
            )
            for doc in documents
        ]
