import fitz  # PyMuPDF

from app.services.document.base import DocumentExtractor, ExtractedDocument
from app.services.document.errors import DocumentExtractionError, EmptyDocumentError


class PDFExtractor(DocumentExtractor):
    def extract(self, file_bytes: bytes, filename: str) -> ExtractedDocument:
        try:
            document = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as exc:
            raise DocumentExtractionError(f"Could not open '{filename}' as a PDF") from exc

        try:
            pages_text = [page.get_text() for page in document]
        except Exception as exc:
            raise DocumentExtractionError(
                f"Failed to read text from '{filename}'"
            ) from exc
        finally:
            document.close()

        raw_text = "\n".join(pages_text).strip()
        if not raw_text:
            raise EmptyDocumentError(f"'{filename}' contains no extractable text")

        return ExtractedDocument(raw_text=raw_text, source_filename=filename)
