"""Stable error mapping for the owner-only association correction."""

from uuid import uuid4

import pytest
from sqlalchemy.exc import DBAPIError

from app.schemas.reference_profiles import ReferenceProfileWrite
from app.services.auth import AuthError
from app.services.reference_profiles import ReferenceProfilesService
from app.tests.unit.test_reference_publication_contracts import _database


@pytest.mark.parametrize(
    "code,status",
    [
        ("REFERENCE_OWNER_INACTIVE", 403),
        ("REFERENCE_PROFILE_VERSION_CONFLICT", 409),
        ("REFERENCE_PROFILE_OPERATION_CONFLICT", 409),
        ("REFERENCE_PROFILE_OCCURRENCE_INVALID", 409),
    ],
)
async def test_profile_maps_known_conflicts(code, status):
    db, _ = _database(error=DBAPIError(None, None, Exception(code), False))
    payload = ReferenceProfileWrite(
        operation_id=uuid4(), expected_version=0, result_id=uuid4(), candidate_id=uuid4(), instagram_handle="@example"
    )
    with pytest.raises(AuthError) as error:
        await ReferenceProfilesService(db).save(uuid4(), uuid4(), uuid4(), uuid4(), payload)
    assert error.value.status == status


async def test_profile_does_not_mask_unexpected_database_failure():
    failure = DBAPIError(None, None, Exception("unexpected"), False)
    db, _ = _database(error=failure)
    payload = ReferenceProfileWrite(
        operation_id=uuid4(), expected_version=0, result_id=uuid4(), candidate_id=uuid4(), instagram_handle="@example"
    )
    with pytest.raises(DBAPIError) as error:
        await ReferenceProfilesService(db).save(uuid4(), uuid4(), uuid4(), uuid4(), payload)
    assert error.value is failure
