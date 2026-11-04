import json
from dataclasses import replace
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr

from app.services.reference_geocoding_cipher import (
    GeocodingCipherError,
    GeocodingPointScope,
    decrypt_geocoding_point,
    encrypt_geocoding_point,
)


def _settings(settings):
    return settings.model_copy(update={"meta_encryption_key": SecretStr(Fernet.generate_key().decode())})


def _scope():
    return GeocodingPointScope(uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), 1)


def test_encrypted_point_is_randomized_private_and_bound_to_full_business_scope(settings):
    settings, scope = _settings(settings), _scope()
    first = encrypt_geocoding_point(settings, scope, -23.5, -46.6)
    second = encrypt_geocoding_point(settings, scope, -23.5, -46.6)
    assert first != second and "-23.5" not in first and "-46.6" not in first
    point = decrypt_geocoding_point(settings, scope, first)
    assert point.latitude == -23.5 and point.longitude == -46.6 and "-23.5" not in repr(point)
    for field in ("tenant", "business", "origin", "effect", "candidate"):
        with pytest.raises(GeocodingCipherError, match="GEOCODING_POINT_UNAVAILABLE"):
            decrypt_geocoding_point(settings, replace(scope, **{field: uuid4()}), first)
    with pytest.raises(GeocodingCipherError, match="GEOCODING_POINT_UNAVAILABLE"):
        decrypt_geocoding_point(settings, replace(scope, context_version=2), first)
    with pytest.raises(GeocodingCipherError, match="GEOCODING_POINT_UNAVAILABLE"):
        decrypt_geocoding_point(_settings(settings), scope, first)
    maximum = replace(scope, context_version=9_223_372_036_854_775_807)
    assert decrypt_geocoding_point(settings, maximum, encrypt_geocoding_point(settings, maximum, 1, 2)).latitude == 1


@pytest.mark.parametrize(
    "scope",
    [
        None,
        GeocodingPointScope("bad", uuid4(), uuid4(), uuid4(), uuid4(), 1),
        GeocodingPointScope(uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), True),
        GeocodingPointScope(uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), 0),
        GeocodingPointScope(uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), 9_223_372_036_854_775_808),
    ],
)
def test_invalid_scope_never_encrypts(settings, scope):
    with pytest.raises(GeocodingCipherError, match="GEOCODING_POINT_SCOPE_INVALID"):
        encrypt_geocoding_point(_settings(settings), scope, 1, 1)


@pytest.mark.parametrize(
    "latitude,longitude",
    [
        (True, 1),
        (1, False),
        (None, 1),
        (float("nan"), 1),
        (float("inf"), 1),
        (91, 1),
        (-91, 1),
        (1, 181),
        (1, -181),
        (10**400, 1),
    ],
)
def test_invalid_coordinates_never_encrypt(settings, latitude, longitude):
    with pytest.raises(GeocodingCipherError, match="GEOCODING_POINT_INVALID"):
        encrypt_geocoding_point(_settings(settings), _scope(), latitude, longitude)


@pytest.mark.parametrize(
    "key,code", [(None, "GEOCODING_POINT_KEY_REQUIRED"), (SecretStr("invalid"), "GEOCODING_POINT_KEY_INVALID")]
)
def test_existing_encryption_key_must_be_configured(settings, key, code):
    with pytest.raises(GeocodingCipherError, match=code):
        encrypt_geocoding_point(settings.model_copy(update={"meta_encryption_key": key}), _scope(), 1, 1)


@pytest.mark.parametrize("ciphertext", [None, "", "x" * 4097, "bad-ciphertext"])
def test_unavailable_ciphertext_fails_closed(settings, ciphertext):
    with pytest.raises(GeocodingCipherError, match="GEOCODING_POINT_UNAVAILABLE"):
        decrypt_geocoding_point(_settings(settings), _scope(), ciphertext)


def test_ciphertext_with_unexpected_or_duplicate_fields_fails_closed(settings):
    settings, scope = _settings(settings), _scope()
    cipher = Fernet(settings.meta_encryption_key.get_secret_value().encode())
    malformed = [b"not-json", b'{"version":1,"version":1}', json.dumps({"version": 1}).encode()]
    for content in malformed:
        with pytest.raises(GeocodingCipherError, match="GEOCODING_POINT_UNAVAILABLE"):
            decrypt_geocoding_point(settings, scope, cipher.encrypt(content).decode())
