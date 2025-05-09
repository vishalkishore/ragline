from fastapi import APIRouter, Depends, HTTPException

from core.logger import log_execution
from query.models import Query, QueryResponse
from query.service import QueryService

router = APIRouter(prefix="/query", tags=["query"])

query_service_dependency = Depends(lambda: QueryService())


@router.post("/", response_model=QueryResponse)
@log_execution
def process_query(query: Query, query_service: QueryService = query_service_dependency):
    try:
        return query_service.process_query(query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {str(e)}"
        ) from e
