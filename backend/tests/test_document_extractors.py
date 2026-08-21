import io

import fitz
import openpyxl
import pytest

from app.services.document.csv_extractor import CSVExtractor
from app.services.document.errors import (
    DocumentExtractionError,
    EmptyDocumentError,
    UnsupportedFileTypeError,
)
from app.services.document.excel_extractor import ExcelExtractor
from app.services.document.factory import get_extractor
from app.services.document.pdf_extractor import PDFExtractor


def _make_pdf_bytes(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def test_pdf_extractor_reads_real_text():
    pdf_bytes = _make_pdf_bytes("Vendor Quote QTE-001 unit price 180")
    result = PDFExtractor().extract(pdf_bytes, "quote.pdf")
    assert "QTE-001" in result.raw_text


def test_pdf_extractor_rejects_malformed_file():
    with pytest.raises(DocumentExtractionError):
        PDFExtractor().extract(b"not a real pdf", "quote.pdf")


def test_pdf_extractor_rejects_empty_text_pdf():
    doc = fitz.open()
    doc.new_page()
    data = doc.tobytes()
    doc.close()
    with pytest.raises(EmptyDocumentError):
        PDFExtractor().extract(data, "blank.pdf")


def test_excel_extractor_reads_rows():
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["SKU", "Description", "Qty", "Unit Price"])
    sheet.append(["6205-2RS", "Industrial Bearing", 500, 205])
    buffer = io.BytesIO()
    workbook.save(buffer)

    result = ExcelExtractor().extract(buffer.getvalue(), "quote.xlsx")
    assert "6205-2RS" in result.raw_text
    assert "205" in result.raw_text


def test_excel_extractor_rejects_malformed_file():
    with pytest.raises(DocumentExtractionError):
        ExcelExtractor().extract(b"not an excel file", "quote.xlsx")


def test_csv_extractor_reads_rows():
    csv_bytes = b"sku,description,quantity,unit_price\n6205-2RS,Bearing,500,165\n"
    result = CSVExtractor().extract(csv_bytes, "quote.csv")
    assert "6205-2RS" in result.raw_text


def test_csv_extractor_rejects_empty_file():
    with pytest.raises(EmptyDocumentError):
        CSVExtractor().extract(b"", "quote.csv")


def test_csv_extractor_falls_back_to_raw_text_for_ragged_real_world_export():
    """Regression test: a real vendor CSV export with a title row, metadata
    rows of varying field count, a line-items table with its own header
    partway down, and footer notes -- pandas.read_csv rejects this shape
    outright (inconsistent column counts), but it's genuinely readable
    content the AI extraction step should still receive, not a hard failure."""
    messy_csv = (
        b"APEX COMPONENTS - SALES QUOTATION\n"
        b"quote_id,AC-2026-119,date,20/08/2026\n"
        b"supplier,Apex Components Pvt Ltd\n"
        b"currency,INR,validity,7 days\n"
        b"\n"
        b"part,description,qty,unit_price,discount,tax,total\n"
        b"BRG-6205,Bearing 6205 ZZ,500,1100,2%,18%,\n"
        b"BRG-6206,Bearing 6206 ZZ,50,1350,,18%,\n"
        b"\n"
        b"NOTE,Prices are ex-works. Freight extra.\n"
    )
    result = CSVExtractor().extract(messy_csv, "messy.csv")
    assert "AC-2026-119" in result.raw_text
    assert "BRG-6205" in result.raw_text
    assert "500" in result.raw_text
    assert "Bearing 6205 ZZ" in result.raw_text


def test_factory_rejects_unsupported_extension():
    with pytest.raises(UnsupportedFileTypeError):
        get_extractor("quote.txt")


def test_factory_returns_correct_extractor_by_extension():
    assert isinstance(get_extractor("quote.pdf"), PDFExtractor)
    assert isinstance(get_extractor("quote.xlsx"), ExcelExtractor)
    assert isinstance(get_extractor("quote.csv"), CSVExtractor)
