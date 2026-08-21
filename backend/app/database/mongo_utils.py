from typing import Any

from bson import ObjectId
from bson.errors import InvalidId


class InvalidObjectIdError(ValueError):
    pass


def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError) as exc:
        raise InvalidObjectIdError(f"'{id_str}' is not a valid id") from exc


def doc_to_response_dict(doc: dict[str, Any]) -> dict[str, Any]:
    """Replace Mongo's _id with a plain string id for API responses."""
    result = dict(doc)
    result["id"] = str(result.pop("_id"))
    return result
