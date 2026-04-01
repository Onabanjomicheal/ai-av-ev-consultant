from pydantic import BaseModel


class IngestRequest(BaseModel):
    directory: str = "./data/raw_docs"
    chunk_size: int = 512
    chunk_overlap: int = 64


class IngestResponse(BaseModel):
    status: str
    chunks_created: int
    files_processed: int
