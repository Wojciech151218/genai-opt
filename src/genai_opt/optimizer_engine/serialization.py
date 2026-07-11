from __future__ import annotations

import importlib
from typing import Any


def type_path(value: type[Any]) -> str:
    return f"{value.__module__}.{value.__qualname__}"


def import_type(path: str) -> type[Any]:
    module_name, _, qualname = path.rpartition(".")
    if not module_name:
        raise ValueError(f"Invalid type path: {path}")
    module = importlib.import_module(module_name)
    value: Any = module
    for part in qualname.split("."):
        value = getattr(value, part)
    if not isinstance(value, type):
        raise TypeError(f"Resolved object is not a type: {path}")
    return value


def serialize_value(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


def deserialize_value(schema: type[Any], value: Any) -> Any:
    if value is None:
        return None
    if hasattr(schema, "model_validate"):
        return schema.model_validate(value)
    return value
