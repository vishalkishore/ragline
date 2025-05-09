# src/query/service.py

from core.logger import log_execution
from document.repository import DocumentRepository
from pipeline.query_processor import QueryProcessor
from query.models import Query, QueryResponse


class QueryService:
    def __init__(self):
        self.processor = QueryProcessor()
        self.document_repository = DocumentRepository()

    @log_execution
    def process_query(self, query: Query) -> QueryResponse:
        """Process a query against documents"""
        # Validate that documents exist
        if query.document_ids:
            for doc_id in query.document_ids:
                document = self.document_repository.get_document_by_id(doc_id)
                if not document:
                    raise ValueError(f"Document with ID {doc_id} not found")

        # Process query
        results = self.processor.process_query(
            query=query.query, document_ids=query.document_ids, top_k=query.top_k
        )

        if not results:
            return QueryResponse(answer="No results found", documents=[])

        # For simplicity, using the first document's answer
        combined_answer = results[0]["answer"]

        # Combine document sources
        documents = []
        for result in results:
            documents.extend(result.get("documents", []))

        # Sort by score
        documents.sort(key=lambda x: x.get("score", 0), reverse=True)

        return QueryResponse(answer=combined_answer, documents=documents)
