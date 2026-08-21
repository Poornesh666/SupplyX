from datetime import date, datetime, timedelta, timezone

import pymongo

from app.core.config import get_settings

FUTURE_DATE = (date.today() + timedelta(days=15)).isoformat()


def _insert_extracted_quote(
    rfq_id: str,
    vendor_id: str,
    unit_price: float,
    delivery_days: int,
) -> None:
    """Direct-pymongo quote insert (bypasses the AI pipeline), mirroring the
    pattern in test_rfq_api.py's _insert_extracted_quote."""
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
                    {
                        "sku": "SKU-1",
                        "description": "Widget",
                        "quantity": 500,
                        "unit": "pcs",
                        "unit_price": unit_price,
                    }
                ],
                "delivery_days": delivery_days,
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


def _create_vendor(client, email, reliability=70, quality=70, payment=70, risk_level="low"):
    resp = client.post(
        "/api/v1/vendors",
        json={
            "name": "Vendor Contact",
            "company": f"Company {email}",
            "email": email,
            "reliability_score": reliability,
            "quality_score": quality,
            "payment_score": payment,
            "risk_level": risk_level,
        },
    )
    assert resp.status_code == 201, resp.text
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


def _setup_two_vendor_rfq(client):
    """Vendor A: cheap price, slow delivery. Vendor B: expensive price, fast
    delivery. Weighting price heavily should favor A; weighting delivery
    heavily should favor B -- this lets us assert the ranking flips."""
    vendor_a = _create_vendor(client, "cheap-slow@example.com")
    vendor_b = _create_vendor(client, "expensive-fast@example.com")
    rfq = client.post("/api/v1/rfqs", json=_rfq_payload([vendor_a, vendor_b])).json()

    _insert_extracted_quote(rfq["id"], vendor_a, unit_price=100.0, delivery_days=25)
    _insert_extracted_quote(rfq["id"], vendor_b, unit_price=400.0, delivery_days=2)

    return rfq["id"], vendor_a, vendor_b


def test_what_if_changes_ranking_with_different_weights(client):
    rfq_id, vendor_a, vendor_b = _setup_two_vendor_rfq(client)

    price_heavy = client.post(
        f"/api/v1/rfqs/{rfq_id}/what-if",
        json={
            "weights": {
                "price": 90,
                "delivery": 2,
                "quality": 2,
                "reliability": 2,
                "payment": 2,
                "risk": 2,
            }
        },
    )
    assert price_heavy.status_code == 200
    price_heavy_body = price_heavy.json()
    price_heavy_winner = next(e for e in price_heavy_body["entries"] if e["rank"] == 1)
    assert price_heavy_winner["vendor_id"] == vendor_a

    delivery_heavy = client.post(
        f"/api/v1/rfqs/{rfq_id}/what-if",
        json={
            "weights": {
                "price": 2,
                "delivery": 90,
                "quality": 2,
                "reliability": 2,
                "payment": 2,
                "risk": 2,
            }
        },
    )
    assert delivery_heavy.status_code == 200
    delivery_heavy_body = delivery_heavy.json()
    delivery_heavy_winner = next(e for e in delivery_heavy_body["entries"] if e["rank"] == 1)
    assert delivery_heavy_winner["vendor_id"] == vendor_b

    assert price_heavy_winner["vendor_id"] != delivery_heavy_winner["vendor_id"]


def test_what_if_does_not_persist_comparison(client):
    """Simulating with custom weights must not change what the plain
    /comparison endpoint (default weights) returns afterwards."""
    rfq_id, vendor_a, vendor_b = _setup_two_vendor_rfq(client)

    baseline = client.get(f"/api/v1/rfqs/{rfq_id}/comparison").json()
    baseline_winner = next(e for e in baseline["entries"] if e["rank"] == 1)["vendor_id"]

    client.post(
        f"/api/v1/rfqs/{rfq_id}/what-if",
        json={
            "weights": {
                "price": 2,
                "delivery": 90,
                "quality": 2,
                "reliability": 2,
                "payment": 2,
                "risk": 2,
            }
        },
    )

    after = client.get(f"/api/v1/rfqs/{rfq_id}/comparison").json()
    after_winner = next(e for e in after["entries"] if e["rank"] == 1)["vendor_id"]
    assert after_winner == baseline_winner


def test_what_if_weights_not_summing_to_100_rejected(client):
    rfq_id, _, _ = _setup_two_vendor_rfq(client)

    resp = client.post(
        f"/api/v1/rfqs/{rfq_id}/what-if",
        json={
            "weights": {
                "price": 50,
                "delivery": 50,
                "quality": 50,
                "reliability": 0,
                "payment": 0,
                "risk": 0,
            }
        },
    )
    assert resp.status_code == 422


def test_what_if_nonexistent_rfq_returns_404(client):
    resp = client.post(
        "/api/v1/rfqs/000000000000000000000000/what-if",
        json={
            "weights": {
                "price": 30,
                "delivery": 20,
                "quality": 15,
                "reliability": 15,
                "payment": 10,
                "risk": 10,
            }
        },
    )
    assert resp.status_code == 404


def test_what_if_before_any_quotes_returns_409(client):
    vendor_id = _create_vendor(client, "lonely@example.com")
    rfq = client.post("/api/v1/rfqs", json=_rfq_payload([vendor_id])).json()

    resp = client.post(
        f"/api/v1/rfqs/{rfq['id']}/what-if",
        json={
            "weights": {
                "price": 30,
                "delivery": 20,
                "quality": 15,
                "reliability": 15,
                "payment": 10,
                "risk": 10,
            }
        },
    )
    assert resp.status_code == 409
