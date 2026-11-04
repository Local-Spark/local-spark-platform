from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.services.reference_search_admission import SearchAdmissionError, search_identity_mac


def test_search_mac_requires_valid_private_key_and_identity():
    key = SecretStr("test-reference-search-key-0123456789abcdef")
    tenant, business, actor, operation = (uuid4() for _ in range(4))
    base = search_identity_mac(key, "test-v1", tenant, business, actor, operation, 1, 5)
    assert len(base) == 64
    assert search_identity_mac(key, "test-v1", tenant, business, actor, operation, 1, 20) != base
    assert search_identity_mac(key, "test-v1", tenant, business, actor, operation, 2, 5) != base
    assert search_identity_mac(key, "test-v2", tenant, business, actor, operation, 1, 5) != base
    with pytest.raises(SearchAdmissionError, match="REFERENCE_SEARCH_KEY_INVALID"):
        search_identity_mac(SecretStr("short"), "test-v1", tenant, business, actor, operation, 1, 5)
    for version, radius in ((0, 5), (True, 5), (1, 7), (1, True)):
        with pytest.raises(SearchAdmissionError, match="REFERENCE_SEARCH_IDENTITY_INVALID"):
            search_identity_mac(key, "test-v1", tenant, business, actor, operation, version, radius)
    with pytest.raises(SearchAdmissionError, match="REFERENCE_SEARCH_IDENTITY_INVALID"):
        search_identity_mac(key, "", tenant, business, actor, operation, 1, 5)
