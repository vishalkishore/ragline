from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from document.models import DocumentResponse
from document.service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])

file_param = File(...)
document_service_dependency = Depends(lambda: DocumentService())


@router.post("/", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = file_param,
    document_service: DocumentService = document_service_dependency,
):
    """Upload and process a PDF document"""
    try:
        return await document_service.upload_document(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {str(e)}"
        ) from e


@router.get("/", response_model=list[DocumentResponse])
def get_all_documents(
    document_service: DocumentService = document_service_dependency,
):
    """Get all documents"""
    return document_service.get_all_documents()


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    document_service: DocumentService = document_service_dependency,
):
    """Get document by ID"""
    document = document_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    return document
