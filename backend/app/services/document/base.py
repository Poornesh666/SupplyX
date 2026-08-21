from abc import ABC, abstractmethod

from pydantic import BaseModel


class ExtractedDocument(BaseModel):
    """Normalized output of any document extractor — plain text the AI
    provider can read, regardless of the source file format."""

    raw_text: str
    source_filename: str


class DocumentExtractor(ABC):
    @abstractmethod
    def extract(self, file_bytes: bytes, filename: str) -> ExtractedDocument: ...
