import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongo_utils import doc_to_response_dict
from app.database.repositories.quote_repository import QuoteRepository
from app.schemas.common import utcnow
from app.schemas.quote import QuoteResponse
from app.services.ai.factory import AIProviderNotConfiguredError, get_ai_provider
from app.services.ai.provider import AIProviderError
from app.services.document.base import ExtractedDocument
from app.services.document.errors import DocumentError
from app.services.document.factory import get_extractor
from app.services.procurement.normalization import normalize_quote
from app.services.procurement.risk_detection import detect_quote_risks
from app.services.rfq import rfq_service

logger = logging.getLogger(__name__)


class VendorNotInvitedError(ValueError):
    pass


async def process_quote_upload(
    db: AsyncIOMotorDatabase,
    *,
    rfq_id: str,
    vendor_id: str,
    filename: str,
    file_bytes: bytes,
) -> QuoteResponse:
    """Upload -> extract -> AI-extract -> validate -> normalize -> detect
    risks -> persist. Runs synchronously within the request; every failure
    mode ends in a persisted quote with status='extraction_failed' and a
    useful error, never a crash and never invented data."""
    rfq = await rfq_service.get_rfq(db, rfq_id)

    if vendor_id not in rfq.invited_vendor_ids:
        raise VendorNotInvitedError(
            f"Vendor '{vendor_id}' was not invited to RFQ '{rfq_id}'"
        )

    file_type = filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"
    base_document = {
        "rfq_id": rfq_id,
        "vendor_id": vendor_id,
        "filename": filename,
        "file_type": file_type,
        "created_at": utcnow(),
    }

    try:
        extractor = get_extractor(filename)
        extracted: ExtractedDocument = extractor.extract(file_bytes, filename)
    except DocumentError as exc:
        logger.info("Document extraction failed for '%s': %s", filename, exc)
        return await _persist_failed(db, base_document, str(exc))

    try:
        provider = get_ai_provider()
        extraction = await provider.extract_quote(extracted.raw_text)
    except (AIProviderError, AIProviderNotConfiguredError) as exc:
        logger.warning("AI extraction failed for '%s': %s", filename, exc)
        return await _persist_failed(db, base_document, str(exc))

    normalized = normalize_quote(extraction, required_quantity=rfq.quantity)
    risks = detect_quote_risks(
        extraction,
        normalized,
        rfq_quantity=rfq.quantity,
        allowed_delivery_days=rfq.allowed_delivery_days,
        required_delivery_date=rfq.required_delivery_date,
    )

    document = {
        **base_document,
        "status": "extracted",
        "extraction_error": None,
        "extraction": extraction.model_dump(mode="json"),
        "normalized": normalized.model_dump(mode="json"),
        "risks": [r.model_dump(mode="json") for r in risks],
    }
    quote = await _persist(db, document)
    await rfq_service.advance_status(db, rfq_id, "quotes_received")

    from app.services.audit.audit_service import record_event

    await record_event(
        db,
        rfq_id,
        "quote_analyzed",
        f"Quote from '{filename}' extracted and analyzed ({len(risks)} risk(s) detected)",
    )

    high_severity = [r for r in risks if r.severity == "high"]
    if high_severity:
        summary = "; ".join(r.description for r in high_severity[:2])
        await record_event(
            db,
            rfq_id,
            "risk_detected",
            f"{len(high_severity)} high-severity risk(s) on '{filename}': {summary}",
        )

    return quote


async def _persist_failed(
    db: AsyncIOMotorDatabase, base_document: dict, error: str
) -> QuoteResponse:
    document = {**base_document, "status": "extraction_failed", "extraction_error": error}
    result = await _persist(db, document)

    from app.services.audit.audit_service import record_event

    await record_event(
        db,
        base_document["rfq_id"],
        "quote_extraction_failed",
        f"Quote extraction failed for '{base_document['filename']}': {error}",
    )

    return result


async def _persist(db: AsyncIOMotorDatabase, document: dict) -> QuoteResponse:
    repo = QuoteRepository(db)
    created = await repo.create(document)
    return QuoteResponse.model_validate(doc_to_response_dict(created))
