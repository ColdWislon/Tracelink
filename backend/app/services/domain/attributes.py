"""Validate and normalize an item's JSONB attributes against its ItemType schema.

A schema is a list of field definitions, each a dict::

    {"key": "priority", "label": "Priority", "type": "enum",
     "required": true, "options": ["P1", "P2", "P3"], "default": "P2"}

Supported ``type`` values: ``string``, ``text``, ``number``, ``bool``, ``enum``.
Pure logic — no DB, no Pydantic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

VALID_TYPES = frozenset({"string", "text", "number", "bool", "enum"})


@dataclass(frozen=True)
class FieldError:
    key: str
    message: str


def _type_ok(field_type: str, value: Any) -> bool:
    match field_type:
        case "string" | "text":
            return isinstance(value, str)
        case "number":
            # bool is a subclass of int; reject it explicitly.
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        case "bool":
            return isinstance(value, bool)
        case "enum":
            return isinstance(value, str)
        case _:
            return False


def validate_attributes(schema: list[dict[str, Any]], values: dict[str, Any]) -> list[FieldError]:
    """Return a list of validation errors (empty means valid)."""
    errors: list[FieldError] = []
    known: set[str] = set()

    for field in schema:
        key = field["key"]
        known.add(key)
        field_type = field.get("type", "string")
        required = bool(field.get("required", False))
        present = key in values and values[key] is not None and values[key] != ""

        if not present:
            if required:
                errors.append(FieldError(key, f"'{key}' is required"))
            continue

        value = values[key]
        if field_type not in VALID_TYPES:
            errors.append(FieldError(key, f"unknown field type '{field_type}'"))
            continue
        if not _type_ok(field_type, value):
            errors.append(FieldError(key, f"'{key}' must be of type {field_type}"))
            continue
        if field_type == "enum":
            options = field.get("options") or []
            if value not in options:
                errors.append(FieldError(key, f"'{key}' must be one of {options}"))

    for key in values:
        if key not in known:
            errors.append(FieldError(key, f"unknown attribute '{key}'"))

    return errors


def normalize_attributes(schema: list[dict[str, Any]], values: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``values`` with defaults applied for missing fields."""
    result = dict(values)
    for field in schema:
        key = field["key"]
        if key not in result and "default" in field:
            result[key] = field["default"]
    return result
