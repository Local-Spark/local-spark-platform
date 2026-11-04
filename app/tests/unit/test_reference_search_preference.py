"""Search scope is explicit and manual address fields are never treated as coordinates."""

import hashlib
import json
from typing import get_args
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr, ValidationError

from app.schemas.editorial_context import ContextUpdate, ReferenceSearchPreference, StateCode
from app.services.editorial_context import _digest
from app.services.editorial_proposals import EditorialProposalService
from app.services.localities import catalog

MANUAL = {
    "scope": "local",
    "radius_km": 5,
    "origin": {"method": "manual", "address": {"city": " Curitiba ", "state_code": "PR"}},
}
DEVICE = {
    "scope": "local",
    "radius_km": 50,
    "origin": {
        "method": "device",
        "coordinates": {"latitude": -25.4, "longitude": -49.2, "accuracy_m": 17.2, "confirmed": True},
    },
}


def test_state_codes_match_local_ibge_catalog() -> None:
    assert set(get_args(StateCode)) == {state.code for state in catalog().states}


def test_valid_scopes_and_manual_is_pending() -> None:
    local = ReferenceSearchPreference.model_validate(MANUAL)
    assert local.origin is not None and local.origin.address is not None
    assert local.origin.address.city == "Curitiba"
    assert local.origin.coordinates is None
    postal = ReferenceSearchPreference.model_validate(
        {**MANUAL, "origin": {"method": "manual", "address": {"postal_code": "80000-000"}}}
    )
    assert postal.origin.address.postal_code == "80000-000"
    assert ReferenceSearchPreference.model_validate(DEVICE).origin.coordinates.accuracy_m == 17.2
    assert ReferenceSearchPreference.model_validate({"scope": "national"}).radius_km is None
    assert ReferenceSearchPreference.model_validate({**MANUAL, "radius_km": 1}).radius_km == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"scope": "national", "radius_km": 5},
        {"scope": "national", "origin": MANUAL["origin"]},
        {"scope": "local", "origin": MANUAL["origin"]},
        {"scope": "local", "radius_km": 5},
        {**MANUAL, "radius_km": 0.9},
        {**MANUAL, "radius_km": 50.1},
        {**MANUAL, "radius_km": float("nan")},
        {**MANUAL, "origin": {"method": "manual"}},
        {**MANUAL, "origin": {"method": "manual", "address": {}}},
        {**MANUAL, "origin": {"method": "manual", "address": {"number": "10"}}},
        {**MANUAL, "origin": {"method": "manual", "address": {"city": "Curitiba"}}},
        {**MANUAL, "origin": {"method": "manual", "address": {"state_code": "PR"}}},
        {**MANUAL, "origin": {"method": "manual", "address": {"city": " "}}},
        {**MANUAL, "origin": {"method": "manual", "address": {"postal_code": "123"}}},
        {**MANUAL, "origin": {"method": "manual", "address": {"state_code": "pr"}}},
        {**MANUAL, "origin": {"method": "manual", "address": {"state_code": "ZZ", "city": "Curitiba"}}},
        {**MANUAL, "origin": {"method": "manual", "address": {"city": "x" * 121}}},
        {
            **MANUAL,
            "origin": {
                "method": "manual",
                "address": {"city": "Rio", "state_code": "RJ"},
                "coordinates": DEVICE["origin"]["coordinates"],
            },
        },
        {**MANUAL, "origin": {"method": "device"}},
        {**DEVICE, "origin": {**DEVICE["origin"], "address": {"postal_code": "80000-000"}}},
        {**DEVICE, "origin": {"method": "device", "coordinates": {"latitude": 91, "longitude": 0, "confirmed": True}}},
        {**DEVICE, "origin": {"method": "device", "coordinates": {"latitude": 0, "longitude": 181, "confirmed": True}}},
        {**DEVICE, "origin": {"method": "device", "coordinates": {"latitude": 0, "longitude": 0, "confirmed": False}}},
        {
            **DEVICE,
            "origin": {
                "method": "device",
                "coordinates": {"latitude": 0, "longitude": 0, "confirmed": True, "accuracy_m": -1},
            },
        },
    ],
)
def test_reject_invalid_search_preference(payload: dict) -> None:
    with pytest.raises(ValidationError):
        ReferenceSearchPreference.model_validate(payload)


def test_legacy_digest_is_unchanged_and_new_preference_is_hashed() -> None:
    old = ContextUpdate(expected_version=0, operation_id=uuid4())
    legacy = old.model_dump(mode="json")
    legacy["preferences"].pop("reference_search")
    legacy["preferences"].pop("cta_destination")
    legacy["preferences"].pop("business_terms")
    legacy["preferences"].pop("business_characteristics")
    encoded = json.dumps(legacy, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    assert _digest(old) == hashlib.sha256(encoded.encode()).hexdigest()
    changed = ContextUpdate.model_validate({**legacy, "preferences": {"reference_search": MANUAL}})
    assert _digest(changed) != _digest(old)


async def test_editorial_model_input_excludes_private_location(settings) -> None:
    context = {
        "facts": [{"id": str(uuid4()), "kind": "product", "statement": "Pão", "source_detail": "Dono"}],
        "preferences": {"goal": "sales", "reference_search": DEVICE, "business_terms": ["Café", "Padaria"]},
    }
    key = Fernet.generate_key()
    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr(key.decode())})
    asset = {
        "kind": "text",
        "ciphertext": Fernet(key).encrypt(b"Pedido ficticio").decode(),
        "transcript_ciphertext": None,
    }
    mapped = Mock(one_or_none=Mock(return_value=asset))
    session = Mock(
        scalar=AsyncMock(return_value=context), execute=AsyncMock(return_value=Mock(mappings=Mock(return_value=mapped)))
    )
    row = {
        "source_asset_id": uuid4(),
        "context_version": 1,
        "tenant_id": uuid4(),
        "business_id": uuid4(),
    }
    data, _ = await EditorialProposalService(cfg, Mock())._inputs(session, row)
    assert data["preferences"]["goal"] == "sales"
    assert data["preferences"]["business_terms"] == ["Café", "Padaria"]
    assert "reference_search" not in data["preferences"]
    assert "-25.4" not in str(data)
    assert "-49.2" not in str(data)
    assert "17.2" not in str(data)
