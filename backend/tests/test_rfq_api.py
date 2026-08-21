from datetime import date, datetime, timedelta, timezone

import pymongo

from app.core.config import get_settings

FUTURE_DATE = (date.today() + timedelta(days=15)).isoformat()
PAST_DATE = (date.today() - timedelta(days=1)).isoformat()


def _insert_extracted_quote(rfq_id: str, vendor_id: str, unit_price: float = 180.0) -> None:
    """Inserts a quote document directly (bypassing the AI pipeline, which
    has no provider configured in tests) so status-transition logic can be
    exercised without a real AI call."""
    settings = get_settings()
    db = pymongo.MongoClient(settings.mongodb_uri)[settings.mongodb_database]
    db.quotes.insert_one(
        {
            "rfq_id": rfq_id,
            "vendor_id": vendor_id,
            "filename": "quote.pdf",
            "file_type": "pdf",
            "status": "extracted",
            "extraction_error": None,
            "created_at": datetime.now(timezone.utc),
            "extraction": {
                "items": [
                    {"sku": "SKU-1", "description": "Widget", "quantity": 500, "unit": "pcs", "unit_price": unit_price}
                ],
                "delivery_days": 10,
                "payment_terms": "Net 30",
                "warranty": "1 year",
                "exclusions": [],
                "risks": [],
                "missing_information": [],
            },
            "normalized": {
                "calculated_subtotal": unit_price * 500,
                "calculated_total": unit_price * 500,
                "document_total": unit_price * 500,
                "total_matches_document": True,
                "normalized_unit_price": unit_price,
            },
            "risks": [],
        }
    )


def _create_vendor(client, email="apex@example.com"):
    resp = client.post(
        "/api/v1/vendors",
        json={
            "name": "Priya Sharma",
            "company": "Apex Industrial Supplies",
            "email": email,
            "reliability_score": 65,
            "quality_score": 70,
            "payment_score": 70,
            "risk_level": "medium",
        },
    )
    return resp.json()["id"]


def _rfq_payload(vendor_ids, delivery_date=FUTURE_DATE):
    return {
        "title": "Industrial Bearing Procurement",
        "description": "Bulk bearing procurement",
        "specifications": "6205-2RS Industrial Bearing",
        "quantity": 500,
        "unit": "pcs",
        "required_delivery_date": delivery_date,
        "invited_vendor_ids": vendor_ids,
    }


def test_create_rfq_generates_rfq_number(client):
    vendor_id = _create_vendor(client)
    resp = client.post("/api/v1/rfqs", json=_rfq_payload([vendor_id]))
    assert resp.status_code == 201
    body = resp.json()
    assert body["rfq_number"].startswith("RFQ-")
    assert body["status"] == "created"
    assert body["allowed_delivery_days"] == 15


def test_rfq_numbers_increment(client):
    vendor_id = _create_vendor(client)
    first = client.post("/api/v1/rfqs", json=_rfq_payload([vendor_id])).json()
    second = client.post("/api/v1/rfqs", json=_rfq_payload([vendor_id])).json()
    assert first["rfq_number"] != second["rfq_number"]


def test_create_rfq_with_unknown_vendor_rejected(client):
    resp = client.post("/api/v1/rfqs", json=_rfq_payload(["000000000000000000000000"]))
    assert resp.status_code == 400


def test_create_rfq_with_past_delivery_date_rejected(client):
    vendor_id = _create_vendor(client)
    resp = client.post("/api/v1/rfqs", json=_rfq_payload([vendor_id], delivery_date=PAST_DATE))
    assert resp.status_code == 422


def test_get_and_list_rfq(client):
    vendor_id = _create_vendor(client)
    created = client.post("/api/v1/rfqs", json=_rfq_payload([vendor_id])).json()

    get_resp = client.get(f"/api/v1/rfqs/{created['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "Industrial Bearing Procurement"

    list_resp = client.get("/api/v1/rfqs")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1


def test_comparison_before_any_quotes_returns_409(client):
    vendor_id = _create_vendor(client)
    created = client.post("/api/v1/rfqs", json=_rfq_payload([vendor_id])).json()

    resp = client.get(f"/api/v1/rfqs/{created['id']}/comparison")
    assert resp.status_code == 409


def test_upload_quote_for_uninvited_vendor_rejected(client):
    invited_vendor = _create_vendor(client, "invited@example.com")
    uninvited_vendor = _create_vendor(client, "uninvited@example.com")
    rfq = client.post("/api/v1/rfqs", json=_rfq_payload([invited_vendor])).json()

    resp = client.post(
        "/api/v1/quotes/upload",
        data={"rfq_id": rfq["id"], "vendor_id": uninvited_vendor},
        files={"file": ("quote.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert resp.status_code == 400


def test_upload_unsupported_file_type_rejected(client):
    vendor_id = _create_vendor(client)
    rfq = client.post("/api/v1/rfqs", json=_rfq_payload([vendor_id])).json()

    resp = client.post(
        "/api/v1/quotes/upload",
        data={"rfq_id": rfq["id"], "vendor_id": vendor_id},
        files={"file": ("quote.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 400


def test_upload_empty_file_rejected(client):
    vendor_id = _create_vendor(client)
    rfq = client.post("/api/v1/rfqs", json=_rfq_payload([vendor_id])).json()

    resp = client.post(
        "/api/v1/quotes/upload",
        data={"rfq_id": rfq["id"], "vendor_id": vendor_id},
        files={"file": ("quote.csv", b"", "text/csv")},
    )
    assert resp.status_code == 400


def test_upload_without_ai_provider_fails_gracefully_not_500(client):
    """Regression test: with no GEMINI_API_KEY/ANTHROPIC_API_KEY configured
    (the case in this test environment), the pipeline must persist a quote
    with status='extraction_failed' and a clear error — never crash with a
    500. This caught a real bug where AIProviderNotConfiguredError wasn't
    caught in quote_pipeline.py."""
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Quote total: 90000")
    pdf_bytes = doc.tobytes()
    doc.close()

    vendor_id = _create_vendor(client)
    rfq = client.post("/api/v1/rfqs", json=_rfq_payload([vendor_id])).json()

    resp = client.post(
        "/api/v1/quotes/upload",
        data={"rfq_id": rfq["id"], "vendor_id": vendor_id},
        files={"file": ("quote.pdf", pdf_bytes, "application/pdf")},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "extraction_failed"
    assert body["extraction_error"]


def test_rfq_status_advances_through_full_pipeline(client):
    """Regression test: status must progress created -> quotes_received ->
    analysis_complete -> recommendation_ready as each stage succeeds. This
    caught a real bug where comparison/recommendation never advanced the
    RFQ past 'quotes_received'."""
    vendor_id = _create_vendor(client)
    rfq = client.post("/api/v1/rfqs", json=_rfq_payload([vendor_id])).json()
    assert rfq["status"] == "created"

    _insert_extracted_quote(rfq["id"], vendor_id)

    comparison_resp = client.get(f"/api/v1/rfqs/{rfq['id']}/comparison")
    assert comparison_resp.status_code == 200
    after_comparison = client.get(f"/api/v1/rfqs/{rfq['id']}").json()
    assert after_comparison["status"] == "analysis_complete"


def test_recommendation_without_ai_provider_returns_503_not_500(client):
    """Regression test: the recommendation endpoint calls the AI provider
    directly; with none configured (this test environment) it must return
    503, not crash with an uncaught 500."""
    vendor_id = _create_vendor(client)
    rfq = client.post("/api/v1/rfqs", json=_rfq_payload([vendor_id])).json()
    _insert_extracted_quote(rfq["id"], vendor_id)

    resp = client.get(f"/api/v1/rfqs/{rfq['id']}/recommendation")
    assert resp.status_code == 503
