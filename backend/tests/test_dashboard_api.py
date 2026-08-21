from datetime import date, datetime, timedelta, timezone

import pymongo
from bson import ObjectId

from app.core.config import get_settings

FUTURE_DATE = (date.today() + timedelta(days=15)).isoformat()


def _db():
    settings = get_settings()
    return pymongo.MongoClient(settings.mongodb_uri)[settings.mongodb_database]


def _create_vendor(client, email):
    resp = client.post(
        "/api/v1/vendors",
        json={
            "name": "Vendor Contact",
            "company": f"Company {email}",
            "email": email,
            "reliability_score": 70,
            "quality_score": 70,
            "payment_score": 70,
            "risk_level": "low",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _create_rfq(client, vendor_id, status="created"):
    resp = client.post(
        "/api/v1/rfqs",
        json={
            "title": "Industrial Bearing Procurement",
            "description": "Bulk bearing procurement",
            "specifications": "6205-2RS Industrial Bearing",
            "quantity": 500,
            "unit": "pcs",
            "required_delivery_date": FUTURE_DATE,
            "invited_vendor_ids": [vendor_id],
        },
    )
    assert resp.status_code == 201, resp.text
    rfq_id = resp.json()["id"]
    if status != "created":
        _db().rfqs.update_one({"_id": ObjectId(rfq_id)}, {"$set": {"status": status}})
    return rfq_id


def _insert_quote(rfq_id, vendor_id, status="extracted", risks=None):
    _db().quotes.insert_one(
        {
            "rfq_id": rfq_id,
            "vendor_id": vendor_id,
            "filename": "quote.pdf",
            "file_type": "pdf",
            "status": status,
            "extraction_error": None if status == "extracted" else "boom",
            "created_at": datetime.now(timezone.utc),
            "extraction": {
                "items": [
                    {"sku": "SKU-1", "description": "Widget", "quantity": 500, "unit": "pcs", "unit_price": 100.0}
                ],
                "delivery_days": 10,
                "payment_terms": "Net 30",
                "warranty": "1 year",
                "exclusions": [],
                "risks": [],
                "missing_information": [],
            }
            if status == "extracted"
            else None,
            "normalized": {
                "calculated_subtotal": 50000.0,
                "calculated_total": 50000.0,
                "document_total": 50000.0,
                "total_matches_document": True,
                "normalized_unit_price": 100.0,
            }
            if status == "extracted"
            else None,
            "risks": risks or [],
        }
    )


def _insert_decision(rfq_id, potential_savings):
    _db().procurement_decisions.insert_one(
        {
            "rfq_id": rfq_id,
            "recommended_vendor_id": "x",
            "recommended_vendor_name": "x",
            "recommended_score": 90.0,
            "alternative_vendor_id": None,
            "alternative_vendor_name": None,
            "alternative_score": None,
            "potential_savings": potential_savings,
            "explanation": {
                "recommendation_summary": "s",
                "why_recommended": [],
                "key_strengths": [],
                "key_risks": [],
                "tradeoffs": [],
                "alternative_vendor": None,
                "confidence": "high",
                "explanation": "e",
            },
            "generated_at": datetime.now(timezone.utc),
            "ranking_signature": [],
        }
    )


def test_dashboard_summary_reflects_seeded_data(client):
    vendor_id = _create_vendor(client, "dash-vendor@example.com")

    active_rfq_1 = _create_rfq(client, vendor_id, status="created")
    active_rfq_2 = _create_rfq(client, vendor_id, status="quotes_received")
    pending_approval_rfq = _create_rfq(client, vendor_id, status="recommendation_ready")
    inactive_rfq = _create_rfq(client, vendor_id, status="po_issued")
    rejected_rfq = _create_rfq(client, vendor_id, status="rejected")

    risk_a = {"type": "t", "severity": "medium", "description": "d", "source": "deterministic", "affected_field": None}
    risk_b = {"type": "t", "severity": "high", "description": "d", "source": "deterministic", "affected_field": None}

    _insert_quote(active_rfq_1, vendor_id, status="extracted", risks=[risk_a, risk_b])
    _insert_quote(active_rfq_2, vendor_id, status="extracted", risks=[risk_a])
    _insert_quote(pending_approval_rfq, vendor_id, status="extraction_failed")

    _insert_decision(active_rfq_1, potential_savings=1500.5)
    _insert_decision(active_rfq_2, potential_savings=None)
    _insert_decision(pending_approval_rfq, potential_savings=299.5)

    resp = client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 200
    body = resp.json()

    # active = NOT in (po_issued, rejected): active_rfq_1, active_rfq_2, pending_approval_rfq = 3
    assert body["active_rfqs"] == 3
    # extracted quotes only: 2
    assert body["quotes_analyzed"] == 2
    # risks: 2 (rfq1) + 1 (rfq2) = 3
    assert body["risks_detected"] == 3
    # savings: 1500.5 + 299.5 = 1800.0 (None skipped)
    assert body["potential_savings"] == 1800.0
    # pending_approvals: status == recommendation_ready -> 1
    assert body["pending_approvals"] == 1

    assert inactive_rfq and rejected_rfq  # seeded, excluded from active count


def test_dashboard_summary_empty_database_returns_zeros(client):
    resp = client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {
        "active_rfqs": 0,
        "quotes_analyzed": 0,
        "risks_detected": 0,
        "potential_savings": 0,
        "pending_approvals": 0,
    }
