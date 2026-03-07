"""
Upload Schemas
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class UploadResponse(BaseModel):
    """Response after file upload"""
    file_id: UUID
    filename: str
    size: int
    chunk_count: int
    uploaded_chunks: int = 0


class ChunkUploadRequest(BaseModel):
    """Request for uploading a chunk"""
    file_id: UUID
    chunk_index: int
    total_chunks: int
    chunk_size: int
    filename: str


class StartGenerationRequest(BaseModel):
    """Request to start report generation"""
    guidelines_file_id: UUID
    project_file_id: UUID


class StartGenerationResponse(BaseModel):
    """Response after starting generation"""
    job_id: UUID
    ws_url: str
    status: str = "queued"

