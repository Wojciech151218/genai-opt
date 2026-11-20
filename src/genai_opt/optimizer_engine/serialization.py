"""Helpers for turning objects and types into checkpoint-safe JSON.

Checkpoints record the import path of a genome class or invocation schema rather
than pickling it, so the file stays readable and cannot execute arbitrary code
on load. The trade-off is that renaming or moving a class invalidates existing
checkpoints.
"""

from __future__ import annotations

import importlib
from typing import Any


def type_path(value: type[Any]) -> str:
    """Return the dotted import path of a type, as stored in checkpoints."""
    return f"{value.__module__}.{value.__qualname__}"


def import_type(path: str) -> type[Any]:
    """Resolve a dotted path produced by :func:`type_path` back into a type.

    Args:
        path: A dotted path such as ``"my_package.my_module.MyGenome"``.

    Returns:
        The resolved type.

    Raises:
        ValueError: If ``path`` has no module component.
        ModuleNotFoundError: If the module cannot be imported, which usually
            means the class was moved or renamed since the checkpoint was made.
        AttributeError: If the module has no such attribute.
        TypeError: If the path resolves to something that is not a type.
    """
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
    """Convert a value to something ``json.dump`` accepts.

    Pydantic models are dumped in JSON mode; anything else is passed through
    unchanged and must already be JSON-serializable.
    """
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


def deserialize_value(schema: type[Any], value: Any) -> Any:
    """Validate a JSON value back into ``schema``.

    Args:
        schema: Target type. Pydantic models are validated; other types cause
            the value to be returned unchanged.
        value: The JSON value read from a checkpoint.

    Returns:
        The validated object, or ``value`` unchanged when ``schema`` is not a
        pydantic model.

    Raises:
        pydantic.ValidationError: If the stored value does not match the schema,
            which is what you see when a schema changed after a checkpoint was
            written.
    """
    if value is None:
        return None
    if hasattr(schema, "model_validate"):
        return schema.model_validate(value)
    return value
