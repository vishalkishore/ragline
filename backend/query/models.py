# src/query/models.py
from typing import Any

from pydantic import BaseModel, Field


class Query(BaseModel):
    query: str
    document_ids: list[str] | None = None  # Filter by document IDs
    top_k: int = Field(default=3, ge=1, le=10)  # Number of chunks to retrieve


class QueryResponse(BaseModel):
    answer: str
    documents: list[dict[str, Any]]  # Sources used to generate the answer
