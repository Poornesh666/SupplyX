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
                        "sku": "SKU-FIN-1",
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


def test_finance_empty_by_default(client):
    summary = client.get("/api/v1/finance/summary").json()
    assert summary == {
        "total_procurement_spend": 0,
        "pending_payments": 0,
        "paid_amount": 0,
        "committed_spend": 0,
    }
    transactions = client.get("/api/v1/finance/transactions").json()
    assert transactions == {"items": []}


def test_finance_reflects_po_statuses(client):
    # draft PO -> pending
    rfq_draft, _ = _rfq_approved(client, email="findraft@example.com")
    po_draft = client.post("/api/v1/purchase-orders", json={"rfq_id": rfq_draft["id"]}).json()

    # issued PO -> pending
    rfq_issued, _ = _rfq_approved(client, email="finissued@example.com")
    po_issued = client.post("/api/v1/purchase-orders", json={"rfq_id": rfq_issued["id"]}).json()
    client.patch(f"/api/v1/purchase-orders/{po_issued['id']}/status", json={"status": "issued"})

    # acknowledged PO -> approved (committed)
    rfq_ack, _ = _rfq_approved(client, email="finack@example.com")
    po_ack = client.post("/api/v1/purchase-orders", json={"rfq_id": rfq_ack["id"]}).json()
    client.patch(f"/api/v1/purchase-orders/{po_ack['id']}/status", json={"status": "issued"})
    client.patch(f"/api/v1/purchase-orders/{po_ack['id']}/status", json={"status": "acknowledged"})

    # received PO -> paid
    rfq_recv, _ = _rfq_approved(client, email="finrecv@example.com")
    po_recv = client.post("/api/v1/purchase-orders", json={"rfq_id": rfq_recv["id"]}).json()
    client.patch(f"/api/v1/purchase-orders/{po_recv['id']}/status", json={"status": "issued"})
    client.patch(f"/api/v1/purchase-orders/{po_recv['id']}/status", json={"status": "acknowledged"})
    client.patch(f"/api/v1/purchase-orders/{po_recv['id']}/status", json={"status": "received"})

    # cancelled PO -> excluded entirely
    rfq_cancel, _ = _rfq_approved(client, email="fincancel@example.com")
    po_cancel = client.post(
        "/api/v1/purchase-orders", json={"rfq_id": rfq_cancel["id"]}
    ).json()
    client.patch(
        f"/api/v1/purchase-orders/{po_cancel['id']}/status", json={"status": "cancelled"}
    )

    po_total = po_draft["total"]  # all POs have the same seeded total

    transactions = client.get("/api/v1/finance/transactions").json()["items"]
    po_ids = {t["po_id"] for t in transactions}
    assert po_draft["id"] in po_ids
    assert po_issued["id"] in po_ids
    assert po_ack["id"] in po_ids
    assert po_recv["id"] in po_ids
    assert po_cancel["id"] not in po_ids

    by_po = {t["po_id"]: t for t in transactions}
    assert by_po[po_draft["id"]]["status"] == "pending"
    assert by_po[po_issued["id"]]["status"] == "pending"
    assert by_po[po_ack["id"]]["status"] == "approved"
    assert by_po[po_recv["id"]]["status"] == "paid"
    for t in transactions:
        assert t["transaction_type"] == "po_commitment"
        assert t["amount"] == po_total

    summary = client.get("/api/v1/finance/summary").json()
    assert summary["total_procurement_spend"] == po_total * 4
    assert summary["pending_payments"] == po_total * 2
    assert summary["committed_spend"] == po_total * 1
    assert summary["paid_amount"] == po_total * 1
