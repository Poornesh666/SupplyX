from datetime import date, datetime, timedelta, timezone

import pymongo

from app.core.config import get_settings

FUTURE_DATE = (date.today() + timedelta(days=15)).isoformat()


def _insert_extracted_quote(rfq_id: str, vendor_id: str, unit_price: float = 180.0) -> None:
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
                        "sku": "SKU-INV-1",
                        "description": "Widget",
                        "quantity": 500,
                        "unit": "pcs",
                        "unit_price": unit_price,
                    }
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


def _rfq_approved(client, email="apex@example.com"):
    vendor_id = _create_vendor(client, email)
    rfq = client.post("/api/v1/rfqs", json=_rfq_payload([vendor_id])).json()
    _insert_extracted_quote(rfq["id"], vendor_id)
    _seed_recommendation_cache(client, rfq["id"])

    approval = client.post(
        f"/api/v1/rfqs/{rfq['id']}/approval",
        json={"decision": "approved", "approver_name": "Jordan Lee"},
    )
    assert approval.status_code == 201, approval.text

    return rfq, vendor_id


def _issued_po(client, email):
    rfq, vendor_id = _rfq_approved(client, email=email)
    po = client.post("/api/v1/purchase-orders", json={"rfq_id": rfq["id"]}).json()
    issue = client.patch(f"/api/v1/purchase-orders/{po['id']}/status", json={"status": "issued"})
    assert issue.status_code == 200, issue.text
    return issue.json()


def test_inventory_empty_by_default(client):
    resp = client.get("/api/v1/inventory")
    assert resp.status_code == 200
    assert resp.json() == {"items": []}


def test_receive_issued_po_increases_inventory_and_marks_received(client):
    po = _issued_po(client, email="receive1@example.com")

    resp = client.post("/api/v1/inventory/receive", json={"po_id": po["id"]})
    assert resp.status_code == 200, resp.text
    items = resp.json()["items"]
    assert len(items) == 1
    item = items[0]
    assert item["sku"] == "SKU-INV-1"
    assert item["quantity"] == 500
    assert item["available_quantity"] == 500

    po_after = client.get(f"/api/v1/purchase-orders/{po['id']}").json()
    assert po_after["status"] == "received"

    # Receiving the same PO a second time should be rejected -- it's now
    # in a terminal "received" status.
    resp2 = client.post("/api/v1/inventory/receive", json={"po_id": po["id"]})
    assert resp2.status_code == 409


def test_receiving_same_sku_twice_across_pos_accumulates_quantity(client):
    po1 = _issued_po(client, email="accum1@example.com")
    po2 = _issued_po(client, email="accum2@example.com")

    r1 = client.post("/api/v1/inventory/receive", json={"po_id": po1["id"]})
    assert r1.status_code == 200
    r2 = client.post("/api/v1/inventory/receive", json={"po_id": po2["id"]})
    assert r2.status_code == 200

    inventory = client.get("/api/v1/inventory").json()["items"]
    matching = [i for i in inventory if i["sku"] == "SKU-INV-1"]
    assert len(matching) == 1
    assert matching[0]["quantity"] == 1000


def test_receive_draft_po_is_rejected(client):
    rfq, _ = _rfq_approved(client, email="draft1@example.com")
    po = client.post("/api/v1/purchase-orders", json={"rfq_id": rfq["id"]}).json()

    resp = client.post("/api/v1/inventory/receive", json={"po_id": po["id"]})
    assert resp.status_code == 409


def test_receive_cancelled_po_is_rejected(client):
    rfq, _ = _rfq_approved(client, email="cancelled1@example.com")
    po = client.post("/api/v1/purchase-orders", json={"rfq_id": rfq["id"]}).json()
    cancel = client.patch(
        f"/api/v1/purchase-orders/{po['id']}/status", json={"status": "cancelled"}
    )
    assert cancel.status_code == 200

    resp = client.post("/api/v1/inventory/receive", json={"po_id": po["id"]})
    assert resp.status_code == 409


def test_receive_unknown_po_returns_404(client):
    resp = client.post(
        "/api/v1/inventory/receive", json={"po_id": "000000000000000000000000"}
    )
    assert resp.status_code == 404
