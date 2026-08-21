"""Seeds vendor master data and the demo RFQ directly via MongoDB (not the
API) so rfq_number/vendor_id are deterministic and match the demo script.
Quotes are intentionally NOT seeded here — upload the generated PDFs in
docs/demo/sample_quotes/ through the real UI so the AI extraction pipeline
actually runs, exactly like the live demo will.

Run with cwd=backend/ (so backend/.env resolves):
  cd backend && .venv/Scripts/python.exe ../scripts/seed_demo_data.py
"""

import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import pymongo

from app.core.config import get_settings

VENDORS = [
    {
        "vendor_id": "VND-0001",
        "name": "Rajesh Kumar",
        "company": "Apex Industrial Supplies",
        "contact": "Rajesh Kumar",
        "email": "sales@apexindustrial.example",
        "phone": "+91 98200 11122",
        "reliability_score": 65,
        "quality_score": 70,
        "payment_score": 70,
        "risk_level": "medium",
    },
    {
        "vendor_id": "VND-0002",
        "name": "Anjali Mehta",
        "company": "Bharat Components Ltd.",
        "contact": "Anjali Mehta",
        "email": "orders@bharatcomponents.example",
        "phone": "+91 98200 33344",
        "reliability_score": 90,
        "quality_score": 85,
        "payment_score": 80,
        "risk_level": "low",
    },
    {
        "vendor_id": "VND-0003",
        "name": "Suresh Nair",
        "company": "Nova Mechanical Systems",
        "contact": "Suresh Nair",
        "email": "sales@novamech.example",
        "phone": "+91 98200 55566",
        "reliability_score": 50,
        "quality_score": 55,
        "payment_score": 60,
        "risk_level": "high",
    },
]


def main() -> None:
    settings = get_settings()
    client = pymongo.MongoClient(settings.mongodb_uri)
    db = client[settings.mongodb_database]

    db.vendors.delete_many({})
    db.rfqs.delete_many({})
    db.quotes.delete_many({})
    db.procurement_decisions.delete_many({})
    db.approvals.delete_many({})
    db.purchase_orders.delete_many({})
    db.inventory.delete_many({})
    db.audit_logs.delete_many({})

    now = datetime.now(timezone.utc)
    for vendor in VENDORS:
        vendor["created_at"] = now
    result = db.vendors.insert_many(VENDORS)
    vendor_ids = [str(_id) for _id in result.inserted_ids]

    required_delivery_date = date.today() + timedelta(days=15)
    rfq = {
        "rfq_number": "RFQ-2026-001",
        "title": "Industrial Bearing Procurement",
        "description": (
            "Bulk procurement of industrial bearings for the assembly line "
            "expansion project."
        ),
        "specifications": "6205-2RS Industrial Bearing, sealed, ABEC-1",
        "quantity": 500,
        "unit": "pcs",
        "required_delivery_date": required_delivery_date.isoformat(),
        "allowed_delivery_days": 15,
        "invited_vendor_ids": vendor_ids,
        "status": "created",
        "created_at": now,
        "updated_at": now,
    }
    rfq_result = db.rfqs.insert_one(rfq)

    print("Seeded vendors:")
    for vendor, vendor_id in zip(VENDORS, vendor_ids):
        print(f"  {vendor_id}  {vendor['company']}")
    print(f"Seeded RFQ: {rfq_result.inserted_id}  {rfq['rfq_number']} — {rfq['title']}")
    print(f"Required delivery date: {required_delivery_date.isoformat()} (15 days out)")


if __name__ == "__main__":
    main()
