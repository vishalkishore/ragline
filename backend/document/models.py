from datetime import datetime

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    filename: str
    upload_time: datetime = Field(default_factory=datetime.now)
    page_count: int | None = None
    document_type: str = "pdf"
    file_size: int | None = None
    user_id: str | None = None


class Document(BaseModel):
    id: str
    metadata: DocumentMetadata
    collection_name: str


class DocumentResponse(BaseModel):
    id: str
    filename: str
    upload_time: datetime
    page_count: int | None = None
    file_size: int | None = None
    status: str = "processed"


class ChunkMetadata(BaseModel):
    document_id: str
    page_num: int | None = None
    chunk_id: str
    chunk_index: int
