from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class DocumentType(str, Enum):
    SCIENTIFIC = "scientific"
    GENERAL = "general"

class DocumentStatus(str, Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class DocumentBase(BaseModel):
    name: str
    type: DocumentType
    status: DocumentStatus
    summary: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: str
    size: Optional[str] = None

    class Config:
        from_attributes = True

class AnalysisRequest(BaseModel):
    documents: List[DocumentCreate]

class AnalysisResponse(BaseModel):
    job_id: str
    status: DocumentStatus
    documents: List[Document]
    consolidated_pdf: Optional[str] = None

class AnalysisStatusResponse(BaseModel):
    job_id: str
    status: DocumentStatus
    documents: List[Document]
    consolidated_pdf: Optional[str] = None
    error: Optional[str] = None

class CustomAnalysisRequest(BaseModel):
    job_id: str
    custom_prompt: str