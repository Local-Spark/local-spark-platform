from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.owner_references import ReferenceCreate
from app.services.owner_references import _request_hash


@pytest.mark.parametrize(
    "value",
    ["@Cafe.Exemplo", "Cafe.Exemplo", "https://instagram.com/Cafe.Exemplo/", "https://www.instagram.com/Cafe.Exemplo"],
)
def test_profile_is_normalized(value):
    profile = ReferenceCreate(operation_id=uuid4(), instagram=value, note="  A vitrine  ")
    assert profile.instagram == "cafe.exemplo"
    assert profile.note == "A vitrine"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "@",
        "ab..cd",
        "abc.",
        ".abc",
        "a" * 31,
        "https://instagram.com/p/example",
        "https://instagram.com/reels",
        "http://instagram.com/perfil",
        "https://instagram.com.evil.com/perfil",
        "https://user@instagram.com/perfil",
        "https://instagram.com/perfil?x=1",
        "https://instagram.com/perfil#x",
        "https://instagram.com/",
        "https://instagram.com/a/b",
        "@inva lido",
        "https://127.0.0.1/x",
    ],
)
def test_invalid_profile_is_rejected(value):
    with pytest.raises(ValidationError):
        ReferenceCreate(operation_id=uuid4(), instagram=value)


def test_empty_note_and_hash_canonicalization():
    assert ReferenceCreate(operation_id=uuid4(), instagram="@perfil", note="   ").note is None
    assert _request_hash("create", {"a": 1, "b": 2}) == _request_hash("create", {"b": 2, "a": 1})
    assert _request_hash("create", {"a": 1}) != _request_hash("remove", {"a": 1})
