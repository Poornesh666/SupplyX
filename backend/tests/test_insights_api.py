from datetime import date, datetime, timedelta, timezone

import pymongo

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


def _create_rfq(client, vendor_id):
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
    return resp.json()["id"]


def _insert_quote(rfq_id, vendor_id, risks=None, warranty="1 year", payment_terms="Net 30"):
    _db().quotes.insert_one(
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
                    {
                        "sku": "SKU-1",
                        "description": "Widget",
                        "quantity": 500,
                        "unit": "pcs",
                        "unit_price": 100.0,
                    }
                ],
                "delivery_days": 10,
                "payment_terms": payment_terms,
                "warranty": warranty,
                "exclusions": [],
                "risks": [],
                "missing_information": [],
            },
            "normalized": {
                "calculated_subtotal": 50000.0,
                "calculated_total": 50000.0,
                "document_total": 50000.0,
                "total_matches_document": True,
                "normalized_unit_price": 100.0,
            },
            "risks": risks or [],
        }
    )


def _insert_decision(rfq_id, potential_savings, vendor_name="Acme", score=90.0):
    _db().procurement_decisions.insert_one(
        {
            "rfq_id": rfq_id,
            "recommended_vendor_id": vendor_name,
            "recommended_vendor_name": vendor_name,
            "recommended_score": score,
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


def test_insights_reflect_seeded_risk_and_savings_data(client):
    vendor_id = _create_vendor(client, "insights-vendor@example.com")
    rfq_id = _create_rfq(client, vendor_id)

    high_risk = {
        "type": "t",
        "severity": "high",
        "description": "d",
        "source": "deterministic",
        "affected_field": None,
    }
    _insert_quote(rfq_id, vendor_id, risks=[high_risk], warranty=None, payment_terms=None)
    _insert_quote(rfq_id, vendor_id, risks=[], warranty="2 years", payment_terms="Net 60")

    _insert_decision(rfq_id, potential_savings=1500.5)

    resp = client.get("/api/v1/insights")
    assert resp.status_code == 200
    items = resp.json()["items"]

    risk_insight = next((i for i in items if i["category"] == "risk"), None)
    assert risk_insight is not None
    assert "1" in risk_insight["summary"]
    assert "high-severity" in risk_insight["summary"]

    quality_insight = next((i for i in items if i["category"] == "quality"), None)
    assert quality_insight is not None
    assert "1" in quality_insight["summary"]

    savings_insight = next((i for i in items if i["category"] == "savings"), None)
    assert savings_insight is not None
    assert "1,500" in savings_insight["summary"] or "1500" in savings_insight["summary"]


def test_insights_include_quotes_analyzed_delivery_risk_and_price_variance(client):
    vendor_id = _create_vendor(client, "insights-variance@example.com")
    rfq_id = _create_rfq(client, vendor_id)

    delivery_risk = {
        "type": "delivery_exceeds_deadline",
        "severity": "high",
        "description": "late",
        "source": "deterministic",
        "affected_field": "delivery_days",
    }
    _insert_quote(rfq_id, vendor_id, risks=[delivery_risk])
    _db().quotes.update_one(
        {"rfq_id": rfq_id, "vendor_id": vendor_id},
        {"$set": {"normalized.normalized_unit_price": 100.0}},
    )
    # A second quote (from an uninvited vendor is fine -- insights only reads
    # the quotes collection directly) at a very different unit price to
    # trigger the price-variance insight.
    second_vendor_id = _create_vendor(client, "insights-variance-2@example.com")
    _insert_quote(rfq_id, second_vendor_id, risks=[])
    _db().quotes.update_one(
        {"rfq_id": rfq_id, "vendor_id": second_vendor_id},
        {"$set": {"normalized.normalized_unit_price": 160.0}},
    )

    resp = client.get(f"/api/v1/insights?rfq_id={rfq_id}")
    assert resp.status_code == 200
    items = resp.json()["items"]

    assert any(i["id"] == "general-quotes-analyzed" and "2" in i["summary"] for i in items)
    assert any(i["id"] == "risk-delivery" for i in items)
    assert any(i["id"] == "quality-price-variance" for i in items)


def test_insights_rfq_id_filters_scope_data(client):
    vendor_id = _create_vendor(client, "insights-vendor-2@example.com")
    rfq_with_risk = _create_rfq(client, vendor_id)
    rfq_without_risk = _create_rfq(client, vendor_id)

    high_risk = {
        "type": "t",
        "severity": "high",
        "description": "d",
        "source": "deterministic",
        "affected_field": None,
    }
    _insert_quote(rfq_with_risk, vendor_id, risks=[high_risk])
    _insert_quote(rfq_without_risk, vendor_id, risks=[])

    resp_risky = client.get(f"/api/v1/insights?rfq_id={rfq_with_risk}")
    assert resp_risky.status_code == 200
    risky_items = resp_risky.json()["items"]
    assert any(i["category"] == "risk" for i in risky_items)
    assert all(i["rfq_id"] == rfq_with_risk for i in risky_items)

    resp_safe = client.get(f"/api/v1/insights?rfq_id={rfq_without_risk}")
    assert resp_safe.status_code == 200
    safe_items = resp_safe.json()["items"]
    assert not any(i["category"] == "risk" for i in safe_items)
