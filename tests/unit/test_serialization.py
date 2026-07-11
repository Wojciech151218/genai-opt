import pytest

from genai_opt.optimizer_engine.serialization import import_type, serialize_value, type_path


class _SampleModel:
    pass


def test_type_path_uses_module_and_qualname() -> None:
    assert type_path(_SampleModel).endswith("test_serialization._SampleModel")


def test_import_type_roundtrip() -> None:
    path = type_path(_SampleModel)
    assert import_type(path) is _SampleModel


def test_serialize_value_handles_pydantic_models() -> None:
    from pydantic import BaseModel

    class Demo(BaseModel):
        value: int

    assert serialize_value(Demo(value=3)) == {"value": 3}


def test_import_type_rejects_invalid_path() -> None:
    with pytest.raises(ValueError, match="Invalid type path"):
        import_type("NotAValidPath")
