from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongo_utils import doc_to_response_dict
from app.database.repositories.vendor_repository import VendorRepository
from app.schemas.common import utcnow
from app.schemas.vendor import VendorCreate, VendorListResponse, VendorResponse


class DuplicateVendorEmailError(ValueError):
    pass


class VendorNotFoundError(ValueError):
    pass


async def create_vendor(db: AsyncIOMotorDatabase, payload: VendorCreate) -> VendorResponse:
    repo = VendorRepository(db)

    existing = await repo.find_by_email(payload.email)
    if existing is not None:
        raise DuplicateVendorEmailError(
            f"A vendor with email '{payload.email}' already exists"
        )

    now = utcnow()
    count = await repo.count()
    document = {
        "vendor_id": f"VND-{count + 1:04d}",
        "name": payload.name,
        "company": payload.company,
        "contact": payload.contact,
        "email": payload.email,
        "phone": payload.phone,
        "reliability_score": payload.reliability_score,
        "quality_score": payload.quality_score,
        "payment_score": payload.payment_score,
        "risk_level": payload.risk_level,
        "created_at": now,
    }
    created = await repo.create(document)
    return VendorResponse.model_validate(doc_to_response_dict(created))


async def list_vendors(db: AsyncIOMotorDatabase) -> VendorListResponse:
    repo = VendorRepository(db)
    items, total = await repo.list_all()
    return VendorListResponse(
        items=[VendorResponse.model_validate(doc_to_response_dict(i)) for i in items],
        total=total,
    )


async def get_vendor(db: AsyncIOMotorDatabase, vendor_id: str) -> VendorResponse:
    repo = VendorRepository(db)
    doc = await repo.get_by_id(vendor_id)
    if doc is None:
        raise VendorNotFoundError(f"Vendor '{vendor_id}' not found")
    return VendorResponse.model_validate(doc_to_response_dict(doc))
