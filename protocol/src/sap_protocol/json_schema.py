"""Small Draft 2020-12 subset used to validate the checked-in SAP fixtures.

This is a conformance harness, not a general replacement for jsonschema. It
implements every keyword used by sap-common.schema.json and fails on unknown
schema structure only where the fixture reaches it.
"""

from __future__ import annotations

from datetime import datetime
import re
from typing import Any, Mapping
from urllib.parse import urlparse
from uuid import UUID

from .validation import ValidationError


class SchemaValidator:
    def __init__(self, root: Mapping[str, Any]) -> None:
        self.root = root

    def validate(self, instance: Any, schema: Mapping[str, Any], path: str = "$") -> None:
        if "$ref" in schema:
            self.validate(instance, self._resolve(schema["$ref"]), path)
            return
        if "anyOf" in schema:
            if not self._matches_any(instance, schema["anyOf"], path):
                raise ValidationError(f"{path}: no anyOf branch matched")
        if "oneOf" in schema:
            matches = sum(self._matches(instance, candidate, path) for candidate in schema["oneOf"])
            if matches != 1:
                raise ValidationError(f"{path}: expected exactly one oneOf match")
        if "allOf" in schema:
            for candidate in schema["allOf"]:
                condition = candidate.get("if")
                if condition is None or self._matches(instance, condition, path):
                    if "then" in candidate:
                        self.validate(instance, candidate["then"], path)
        if "const" in schema and instance != schema["const"]:
            raise ValidationError(f"{path}: expected constant {schema['const']!r}")
        if "enum" in schema and instance not in schema["enum"]:
            raise ValidationError(f"{path}: value is outside enum")
        if "type" in schema:
            allowed = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
            if not any(self._is_type(instance, item) for item in allowed):
                raise ValidationError(f"{path}: expected type {allowed}")
        if isinstance(instance, dict):
            self._validate_object(instance, schema, path)
        elif isinstance(instance, list):
            self._validate_array(instance, schema, path)
        elif isinstance(instance, str):
            self._validate_string(instance, schema, path)
        elif isinstance(instance, (int, float)) and not isinstance(instance, bool):
            self._validate_number(instance, schema, path)

    def _resolve(self, reference: str) -> Mapping[str, Any]:
        fragment = reference.split("#", 1)[-1]
        if not fragment.startswith("/"):
            raise ValidationError(f"unsupported schema reference: {reference}")
        value: Any = self.root
        for token in fragment.lstrip("/").split("/"):
            value = value[token.replace("~1", "/").replace("~0", "~")]
        if not isinstance(value, dict):
            raise ValidationError(f"schema reference is not an object: {reference}")
        return value

    def _matches(self, instance: Any, schema: Mapping[str, Any], path: str) -> bool:
        try:
            self.validate(instance, schema, path)
            return True
        except ValidationError:
            return False

    def _matches_any(self, instance: Any, schemas: list[Mapping[str, Any]], path: str) -> bool:
        return any(self._matches(instance, schema, path) for schema in schemas)

    @staticmethod
    def _is_type(value: Any, expected: str) -> bool:
        return {
            "null": value is None,
            "object": isinstance(value, dict),
            "array": isinstance(value, list),
            "string": isinstance(value, str),
            "boolean": isinstance(value, bool),
            "integer": isinstance(value, int) and not isinstance(value, bool),
            "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        }.get(expected, False)

    def _validate_object(self, value: dict[str, Any], schema: Mapping[str, Any], path: str) -> None:
        required = schema.get("required", ())
        missing = [key for key in required if key not in value]
        if missing:
            raise ValidationError(f"{path}: missing required fields {missing}")
        properties = schema.get("properties", {})
        for key, item in value.items():
            if key in properties:
                self.validate(item, properties[key], f"{path}.{key}")
            elif schema.get("additionalProperties") is False:
                raise ValidationError(f"{path}.{key}: additional property forbidden")
            elif isinstance(schema.get("additionalProperties"), dict):
                self.validate(item, schema["additionalProperties"], f"{path}.{key}")

    def _validate_array(self, value: list[Any], schema: Mapping[str, Any], path: str) -> None:
        if len(value) < schema.get("minItems", 0):
            raise ValidationError(f"{path}: too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ValidationError(f"{path}: too many items")
        if schema.get("uniqueItems") and len({repr(item) for item in value}) != len(value):
            raise ValidationError(f"{path}: duplicate items")
        if "items" in schema:
            for index, item in enumerate(value):
                self.validate(item, schema["items"], f"{path}[{index}]")

    @staticmethod
    def _validate_number(value: float, schema: Mapping[str, Any], path: str) -> None:
        if "minimum" in schema and value < schema["minimum"]:
            raise ValidationError(f"{path}: below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            raise ValidationError(f"{path}: above maximum")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            raise ValidationError(f"{path}: below exclusive minimum")

    @staticmethod
    def _validate_string(value: str, schema: Mapping[str, Any], path: str) -> None:
        if len(value) < schema.get("minLength", 0):
            raise ValidationError(f"{path}: string too short")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise ValidationError(f"{path}: string too long")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            raise ValidationError(f"{path}: pattern mismatch")
        format_name = schema.get("format")
        try:
            if format_name == "uuid":
                UUID(value)
            elif format_name == "date-time":
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    raise ValueError
            elif format_name == "uri" and not urlparse(value).scheme:
                raise ValueError
        except (ValueError, AttributeError) as exc:
            raise ValidationError(f"{path}: invalid {format_name}") from exc
