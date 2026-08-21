"""Generates 3 realistic, intentionally-differentiated vendor quote PDFs for
the SupplyX demo (RFQ-2026-001, Industrial Bearing Procurement, 500 pcs,
15-day delivery window). Upload these through the RFQ detail page to exercise
the real extraction pipeline — they are not inserted into MongoDB directly.

Run with any Python that has PyMuPDF (the backend venv has it):
  cd backend && .venv/Scripts/python.exe ../scripts/generate_demo_quotes.py
"""

from datetime import date, timedelta
from pathlib import Path

import fitz  # PyMuPDF

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "demo" / "sample_quotes"

TODAY = date.today()
QUOTE_DATE = TODAY.isoformat()


def _write_pdf(filename: str, lines: list[str]) -> None:
    doc = fitz.open()
    page = doc.new_page()
    y = 60
    for line in lines:
        size = 14 if line.isupper() and len(line) < 60 else 10.5
        page.insert_text((56, y), line, fontsize=size)
        y += 20 if size > 12 else 16
        if y > 780:
            page = doc.new_page()
            y = 60
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT_DIR / filename)
    doc.close()
    print(f"Wrote {OUTPUT_DIR / filename}")


def apex_quote() -> None:
    _write_pdf(
        "apex-industrial-supplies-quote.pdf",
        [
            "APEX INDUSTRIAL SUPPLIES",
            "Plot 14, MIDC Industrial Area, Pune, Maharashtra 411019",
            "sales@apexindustrial.example | +91 98200 11122",
            "",
            "QUOTATION",
            f"Quote Number: APX-QT-2451",
            f"Quote Date: {QUOTE_DATE}",
            "Validity: 30 days from quote date",
            "Currency: INR",
            "",
            "Bill To: SupplyX Procurement (RFQ-2026-001)",
            "Subject: Industrial Bearing Procurement",
            "",
            "LINE ITEMS",
            "SKU: 6205-2RS | Description: 6205-2RS Industrial Bearing, sealed, ABEC-1",
            "Quantity: 500 pcs | Unit Price: INR 180.00",
            "",
            "Subtotal: INR 90,000.00",
            "Total: INR 90,000.00",
            "",
            "TERMS",
            "Delivery Time: 18 days from order confirmation",
            "Payment Terms: Net 30",
            "Warranty: 1 year manufacturer warranty",
            "Minimum Order Quantity (MOQ): 100 units",
            "",
            "Thank you for the opportunity to quote.",
        ],
    )


def bharat_quote() -> None:
    _write_pdf(
        "bharat-components-quote.pdf",
        [
            "BHARAT COMPONENTS LTD.",
            "Sector 8, Industrial Estate, Faridabad, Haryana 121006",
            "orders@bharatcomponents.example | +91 98200 33344",
            "",
            "QUOTATION",
            f"Quote Number: BCL-2026-0876",
            f"Quote Date: {QUOTE_DATE}",
            "Validity: 30 days from quote date",
            "Currency: INR",
            "",
            "Bill To: SupplyX Procurement (RFQ-2026-001)",
            "Subject: Industrial Bearing Procurement",
            "",
            "LINE ITEMS",
            "SKU: 6205-2RS | Description: 6205-2RS Industrial Bearing, sealed, ABEC-1",
            "Quantity: 500 pcs | Unit Price: INR 205.00",
            "",
            "Subtotal: INR 102,500.00",
            "Total: INR 102,500.00",
            "",
            "TERMS",
            "Delivery Time: 10 days from order confirmation",
            "Payment Terms: Net 45",
            "Warranty: 2 years manufacturer warranty",
            "Minimum Order Quantity (MOQ): 50 units",
            "",
            "We look forward to a long-term partnership.",
        ],
    )


def nova_quote() -> None:
    _write_pdf(
        "nova-mechanical-quote.pdf",
        [
            "NOVA MECHANICAL SYSTEMS",
            "Unit 7, GIDC Estate, Ahmedabad, Gujarat 382445",
            "sales@novamech.example | +91 98200 55566",
            "",
            "QUOTATION",
            f"Quote Number: NMS/Q/3390",
            f"Quote Date: {QUOTE_DATE}",
            "Validity: 30 days from quote date",
            "Currency: INR",
            "",
            "Bill To: SupplyX Procurement (RFQ-2026-001)",
            "Subject: Industrial Bearing Procurement",
            "",
            "LINE ITEMS",
            "SKU: 6205-2RS | Description: 6205-2RS Industrial Bearing, sealed, ABEC-1",
            "Quantity: 500 pcs | Unit Price: INR 165.00",
            "",
            "Subtotal: INR 82,500.00",
            "Total: INR 82,500.00",
            "",
            "TERMS",
            "Delivery Time: 20 days from order confirmation",
            "Minimum Order Quantity (MOQ): 600 units",
            "",
            "EXCLUSIONS",
            "Prices exclude shipping and applicable taxes.",
            "No warranty on bulk orders.",
            "",
            "Rates valid for bulk commitment only.",
        ],
    )


if __name__ == "__main__":
    apex_quote()
    bharat_quote()
    nova_quote()
    print(f"\n3 demo quote PDFs generated in {OUTPUT_DIR}")
