import csv
import io

import pandas as pd

from app.services.document.base import DocumentExtractor, ExtractedDocument
from app.services.document.errors import EmptyDocumentError


class CSVExtractor(DocumentExtractor):
    def extract(self, file_bytes: bytes, filename: str) -> ExtractedDocument:
        try:
            df = pd.read_csv(io.BytesIO(file_bytes))
            if df.empty:
                raise EmptyDocumentError(f"'{filename}' contains no rows")
            raw_text = df.to_csv(sep="|", index=False)
            return ExtractedDocument(raw_text=raw_text, source_filename=filename)
        except pd.errors.EmptyDataError as exc:
            raise EmptyDocumentError(f"'{filename}' contains no data") from exc
        except EmptyDocumentError:
            raise
        except Exception:
            # Real vendor CSV exports are frequently irregular: a title row,
            # metadata rows with a varying field count, a line-items table
            # with its own header partway down, footer notes. pandas requires
            # a uniform column count and raises on exactly this shape. Since
            # the only consumer of raw_text is the AI extraction prompt (not
            # a DataFrame), fall back to reading it as plain delimited text
            # line-by-line -- still real, unaltered file content, just not
            # forced into a rectangular table.
            return self._extract_as_raw_text(file_bytes, filename)

    def _extract_as_raw_text(self, file_bytes: bytes, filename: str) -> ExtractedDocument:
        try:
            text = file_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = file_bytes.decode("latin-1")

        lines = []
        for row in csv.reader(io.StringIO(text)):
            cells = [cell for cell in row if cell.strip()]
            if cells:
                lines.append(" | ".join(cells))

        raw_text = "\n".join(lines).strip()
        if not raw_text:
            raise EmptyDocumentError(f"'{filename}' contains no data")

        return ExtractedDocument(raw_text=raw_text, source_filename=filename)
