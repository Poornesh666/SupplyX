from pydantic import BaseModel, Field


class ExtractedItem(BaseModel):
    sku: str | None = None
    description: str = ""
    quantity: float = Field(ge=0, default=0)
    unit: str | None = None
    unit_price: float = Field(ge=0, default=0)


class QuoteExtraction(BaseModel):
    """Structured facts pulled from a vendor quote document by the AI provider.

    The AI only extracts what it reads — it must not compute totals or
    scores. Every field is optional/defaulted because source documents are
    inconsistent; missing fields become deterministic risks downstream
    rather than invented values.
    """

    vendor_name: str | None = None
    quote_number: str | None = None
    quote_date: str | None = None
    validity_days: int | None = None
    currency: str | None = None
    items: list[ExtractedItem] = Field(default_factory=list)
    subtotal: float | None = None
    discount: float | None = None
    tax: float | None = None
    shipping: float | None = None
    total: float | None = None
    delivery_days: int | None = None
    payment_terms: str | None = None
    warranty: str | None = None
    moq: int | None = None
    exclusions: list[str] = Field(default_factory=list)
    notes: str | None = None
    risks: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


GEMINI_EXTRACTION_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "vendor_name": {"type": "string", "nullable": True},
        "quote_number": {"type": "string", "nullable": True},
        "quote_date": {"type": "string", "nullable": True},
        "validity_days": {"type": "integer", "nullable": True},
        "currency": {"type": "string", "nullable": True},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "sku": {"type": "string", "nullable": True},
                    "description": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unit": {"type": "string", "nullable": True},
                    "unit_price": {"type": "number"},
                },
                "required": ["description", "quantity", "unit_price"],
            },
        },
        "subtotal": {"type": "number", "nullable": True},
        "discount": {"type": "number", "nullable": True},
        "tax": {"type": "number", "nullable": True},
        "shipping": {"type": "number", "nullable": True},
        "total": {"type": "number", "nullable": True},
        "delivery_days": {"type": "integer", "nullable": True},
        "payment_terms": {"type": "string", "nullable": True},
        "warranty": {"type": "string", "nullable": True},
        "moq": {"type": "integer", "nullable": True},
        "exclusions": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "string", "nullable": True},
        "risks": {"type": "array", "items": {"type": "string"}},
        "missing_information": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["items"],
}
