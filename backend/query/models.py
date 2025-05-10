from typing import Any

from pydantic import BaseModel, Field


class Query(BaseModel):
    query: str
    document_ids: list[str] | None = None 
    top_k: int = Field(default=3, ge=1, le=10) 


class QueryResponse(BaseModel):
    answer: str
    documents: list[dict[str, Any]] 
