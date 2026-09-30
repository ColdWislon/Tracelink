from __future__ import annotations

from app.services.domain.attributes import normalize_attributes, validate_attributes

SCHEMA = [
    {
        "key": "priority",
        "label": "Priority",
        "type": "enum",
        "required": True,
        "options": ["P1", "P2", "P3"],
        "default": "P2",
    },
    {"key": "rationale", "label": "Rationale", "type": "text"},
    {"key": "cycles", "label": "Cycles", "type": "number"},
    {"key": "safety", "label": "Safety", "type": "bool"},
]


def test_valid_attributes() -> None:
    values = {"priority": "P1", "rationale": "latency bound", "cycles": 16, "safety": True}
    assert validate_attributes(SCHEMA, values) == []


def test_required_missing() -> None:
    errors = validate_attributes(SCHEMA, {})
    assert [e.key for e in errors] == ["priority"]


def test_enum_out_of_range() -> None:
    errors = validate_attributes(SCHEMA, {"priority": "P9"})
    assert errors and errors[0].key == "priority"


def test_type_mismatches() -> None:
    errors = validate_attributes(SCHEMA, {"priority": "P1", "cycles": "sixteen"})
    assert any(e.key == "cycles" for e in errors)


def test_bool_not_accepted_as_number() -> None:
    errors = validate_attributes(SCHEMA, {"priority": "P1", "cycles": True})
    assert any(e.key == "cycles" for e in errors)


def test_unknown_attribute() -> None:
    errors = validate_attributes(SCHEMA, {"priority": "P1", "bogus": 1})
    assert any(e.key == "bogus" for e in errors)


def test_normalize_applies_defaults() -> None:
    assert normalize_attributes(SCHEMA, {})["priority"] == "P2"
    assert normalize_attributes(SCHEMA, {"priority": "P1"})["priority"] == "P1"
