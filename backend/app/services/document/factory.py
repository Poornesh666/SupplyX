from app.services.document.base import DocumentExtractor
from app.services.document.csv_extractor import CSVExtractor
from app.services.document.errors import UnsupportedFileTypeError
from app.services.document.excel_extractor import ExcelExtractor
from app.services.document.pdf_extractor import PDFExtractor

_EXTRACTORS_BY_SUFFIX: dict[str, type[DocumentExtractor]] = {
    "pdf": PDFExtractor,
    "xlsx": ExcelExtractor,
    "xls": ExcelExtractor,
    "csv": CSVExtractor,
}

SUPPORTED_EXTENSIONS = tuple(_EXTRACTORS_BY_SUFFIX.keys())


def get_extractor(filename: str) -> DocumentExtractor:
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    extractor_cls = _EXTRACTORS_BY_SUFFIX.get(suffix)
    if extractor_cls is None:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '.{suffix}' — allowed: "
            f"{', '.join(SUPPORTED_EXTENSIONS)}"
        )
    return extractor_cls()
