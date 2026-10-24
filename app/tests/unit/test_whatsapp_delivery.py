"""Receipt parsing rejects unsupported or unsafe provider metadata."""

from app.services.whatsapp_delivery import receipt


def test_receipt_accepts_only_supported_states_and_safe_codes():
    for payload in (
        None,
        [],
        {},
        {"id": 1, "status": "sent"},
        {"id": "", "status": "sent"},
        {"id": "wamid", "status": []},
        {"id": "wamid", "status": "unknown"},
    ):
        assert receipt(payload) is None
    assert receipt({"id": "wamid", "status": "sent"}) == ("wamid", "sent", None)
    assert receipt({"id": "wamid", "status": "failed", "errors": [{"code": 131031}]}) == ("wamid", "failed", "131031")
    for errors in ("wrong", [], [{}], [{"code": "private"}], [{"code": -1}], [{"code": 10**12}]):
        assert receipt({"id": "wamid", "status": "failed", "errors": errors}) == ("wamid", "failed", None)
    assert receipt({"id": "wamid", "status": "read", "errors": [{"code": 131031}]}) == ("wamid", "read", None)
