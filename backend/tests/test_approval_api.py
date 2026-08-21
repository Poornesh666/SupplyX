from datetime import date, datetime, timedelta, timezone

import pymongo

from app.core.config import get_settings

FUTURE_DATE = (date.today() + timedelta(days=15)).isoformat()


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


def _fake_explanation():
    return {
        "recommendation_summary": "Vendor offers the best combined value.",
        "why_recommended": ["Lowest total cost"],
        "key_strengths": ["Reliable delivery"],
        "key_risks": [],
        "tradeoffs": [],
        "alternative_vendor": None,
        "confidence": "high",
        "explanation": "Deterministic scoring favors this vendor.",
    }


def _seed_recommendation_cache(client, rfq_id: str) -> None:
    """Reaches 'recommendation_ready' without calling the (unconfigured) AI
    provider: builds the real, deterministic comparison through the API,
    then inserts a matching procurement_decisions cache document directly
    so get_or_generate_recommendation finds a signature match and returns
    the cached explanation instead of calling the AI provider."""
    comparison = client.get(f"/api/v1/rfqs/{rfq_id}/comparison").json()
    winner = comparison["entries"][0]
    alternative = comparison["entries"][1] if len(comparison["entries"]) > 1 else None

    settings = get_settings()
    db = pymongo.MongoClient(settings.mongodb_uri)[settings.mongodb_database]
    db.procurement_decisions.update_one(
        {"rfq_id": rfq_id},
        {
            "$set": {
                "rfq_id": rfq_id,
                "recommended_vendor_id": winner["vendor_id"],
                "recommended_vendor_name": winner["vendor_name"],
                "recommended_score": winner["total_score"],
                "alternative_vendor_id": alternative["vendor_id"] if alternative else None,
                "alternative_vendor_name": alternative["vendor_name"] if alternative else None,
                "alternative_score": alternative["total_score"] if alternative else None,
                "potential_savings": None,
                "explanation": _fake_explanation(),
                "generated_at": datetime.now(timezone.utc),
                "ranking_signature": [[e["vendor_id"], e["total_score"]] for e in comparison["entries"]],
            }
        },
        upsert=True,
    )

    rec_resp = client.get(f"/api/v1/rfqs/{rfq_id}/recommendation")
    assert rec_resp.status_code == 200, rec_resp.text


def _rfq_at_recommendation_ready(client, email="apex@example.com"):
    vendor_id = _create_vendor(client, email)
    rfq = client.post("/api/v1/rfqs", json=_rfq_payload([vendor_id])).json()
    _insert_extracted_quote(rfq["id"], vendor_id)
    _seed_recommendation_cache(client, rfq["id"])
    return rfq, vendor_id


def test_approve_recommendation_happy_path(client):
    rfq, vendor_id = _rfq_at_recommendation_ready(client)

    resp = client.post(
        f"/api/v1/rfqs/{rfq['id']}/approval",
        json={"decision": "approved", "approver_name": "Jordan Lee", "note": "Looks good"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["decision"] == "approved"
    assert body["recommended_vendor_id"] == vendor_id
    assert body["approver_name"] == "Jordan Lee"

    rfq_after = client.get(f"/api/v1/rfqs/{rfq['id']}").json()
    assert rfq_after["status"] == "approved"

    get_resp = client.get(f"/api/v1/rfqs/{rfq['id']}/approval")
    assert get_resp.status_code == 200
    assert get_resp.json()["decision"] == "approved"


def test_comparison_and_recommendation_still_work_after_approval(client):
    """Regression test: comparison_service/recommendation_service call
    rfq_service.advance_status as a side effect, which used to crash with
    'approved' is not in list once the RFQ moved past the linear P0 status
    pipeline into the branching approve/reject states."""
    rfq, _ = _rfq_at_recommendation_ready(client, email="regression@example.com")
    approve_resp = client.post(
        f"/api/v1/rfqs/{rfq['id']}/approval",
        json={"decision": "approved", "approver_name": "Jordan Lee"},
    )
    assert approve_resp.status_code == 201

    comparison_resp = client.get(f"/api/v1/rfqs/{rfq['id']}/comparison")
    assert comparison_resp.status_code == 200

    recommendation_resp = client.get(f"/api/v1/rfqs/{rfq['id']}/recommendation")
    assert recommendation_resp.status_code == 200

    rfq_after = client.get(f"/api/v1/rfqs/{rfq['id']}").json()
    assert rfq_after["status"] == "approved"


def test_reject_recommendation(client):
    rfq, _ = _rfq_at_recommendation_ready(client, email="reject@example.com")

    resp = client.post(
        f"/api/v1/rfqs/{rfq['id']}/approval",
        json={"decision": "rejected", "approver_name": "Jordan Lee"},
    )
    assert resp.status_code == 201
    assert resp.json()["decision"] == "rejected"

    rfq_after = client.get(f"/api/v1/rfqs/{rfq['id']}").json()
    assert rfq_after["status"] == "rejected"


def test_approving_twice_is_rejected(client):
    rfq, _ = _rfq_at_recommendation_ready(client, email="twice@example.com")

    first = client.post(
        f"/api/v1/rfqs/{rfq['id']}/approval",
        json={"decision": "approved", "approver_name": "Jordan Lee"},
    )
    assert first.status_code == 201

    second = client.post(
        f"/api/v1/rfqs/{rfq['id']}/approval",
        json={"decision": "approved", "approver_name": "Jordan Lee"},
    )
    assert second.status_code == 409


def test_approval_before_recommendation_ready_is_rejected(client):
    vendor_id = _create_vendor(client, "early@example.com")
    rfq = client.post("/api/v1/rfqs", json=_rfq_payload([vendor_id])).json()

    resp = client.post(
        f"/api/v1/rfqs/{rfq['id']}/approval",
        json={"decision": "approved", "approver_name": "Jordan Lee"},
    )
    assert resp.status_code == 409


def test_get_approval_without_decision_returns_404(client):
    rfq, _ = _rfq_at_recommendation_ready(client, email="nodecision@example.com")

    resp = client.get(f"/api/v1/rfqs/{rfq['id']}/approval")
    assert resp.status_code == 404


def test_approval_for_unknown_rfq_returns_404(client):
    resp = client.post(
        "/api/v1/rfqs/000000000000000000000000/approval",
        json={"decision": "approved", "approver_name": "Jordan Lee"},
    )
    assert resp.status_code == 404
