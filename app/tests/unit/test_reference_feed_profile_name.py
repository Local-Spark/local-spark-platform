import pytest

from app.adapters.apify_instagram_feed import _posts, _profile_name


def row(name="Nome Instagram", owner="fixture"):
    return {"id": "post", "type": "Image", "ownerUsername": owner, "ownerFullName": name, "caption": "caption"}


def test_only_matching_instagram_owner_can_supply_name_from_same_response():
    rows = [
        None,
        {"title": "Google Maps title"},
        row("Other", "other"),
        row("ignored", "@bad/handle"),
        row(" Nome Instagram "),
        row(),
    ]
    assert _profile_name(rows, "fixture") == "Nome Instagram"
    assert _posts([row()], "fixture", 20, provider_partial=False).profile_name == "Nome Instagram"
    assert _posts([{**row(), "caption": None}], "fixture", 20, provider_partial=False).profile_name == "Nome Instagram"


@pytest.mark.parametrize(
    "name", [1, "", "   ", "a" * 201, "unsafe\nname", "unsafe\x7fname", "unsafe\x85name", "\ud800"]
)
def test_invalid_matching_name_never_changes_fallback(name):
    assert _profile_name([row(name)], "fixture") is None


def test_conflicting_or_missing_names_fall_back_to_profile_handle():
    assert _profile_name([row(), row("Conflicting")], "fixture") is None
    assert _profile_name([{"title": "Name from Maps"}, row(None)], "fixture") is None
