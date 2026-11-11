"""Elements must bind to the captured catalogue and isolated render bytes."""

import hashlib
from dataclasses import replace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.adapters.motion_html_renderer import MotionRenderError, _prepare
from app.schemas.motion_production import HTMLMotionComposition, MotionRequest
from app.services.auth import AuthError
from app.services.motion_elements import elements_contract, elements_hash, runtime_bytes
from app.tests.unit.test_motion_ai import provider, request
from app.tests.unit.test_motion_html_renderer import bundle
from app.tests.unit.test_motion_plan import context, planned
from app.tests.unit.test_motion_scene_direction import validate


def test_library_is_counted_and_bound_to_render_bytes(tmp_path):
    ctx = context()
    digest = elements_hash(ctx)
    assert digest == hashlib.sha256(runtime_bytes()).hexdigest()
    payload = provider().build_request(replace(request(), context=ctx))
    assert digest in payload["input"][0]["content"][0]["text"]
    assert "MotionElementsV1.mount" in payload["input"][0]["content"][0]["text"]
    modern = bundle(element_runtime_sha256=digest)
    _prepare(modern, tmp_path / "modern")
    assert (tmp_path / "modern/scene.js").read_bytes() == runtime_bytes() + b"\n;\n" + modern.scene_init.encode()
    _prepare(bundle(), tmp_path / "old")
    assert (tmp_path / "old/scene.js").read_text() == bundle().scene_init
    with pytest.raises(MotionRenderError, match="ELEMENTS_VERSION_UNAVAILABLE"):
        _prepare(bundle(element_runtime_sha256="0" * 64), tmp_path / "invalid")
    assert elements_hash({}) is None


@pytest.mark.parametrize("field,value", [("sha256", "0" * 64), ("items", []), ("api", "changed")])
def test_captured_library_cannot_silently_change(field, value):
    with pytest.raises(AuthError, match="ELEMENTS_VERSION_UNAVAILABLE"):
        elements_hash({"creative_contract": {"element_library": {**elements_contract(), field: value}}})


@pytest.mark.parametrize("change", ["valid", "unknown", "missing_library", "wrong_role", "unexpected"])
def test_only_available_components_can_be_declared(change):
    ctx = context()
    data = planned().model_dump(mode="json")
    data["motion_plan"]["scenes"][0]["elements"][0]["role"] = "graphic"
    element = data["scene_direction"]["scenes"][0]["elements"][0]
    element.update(construction="component", component_id="cup")
    if change == "unknown":
        element["component_id"] = "invented"
    elif change == "missing_library":
        ctx["creative_contract"].pop("element_library")
    elif change == "wrong_role":
        data["motion_plan"]["scenes"][0]["elements"][0]["role"] = "text"
    elif change == "unexpected":
        element["construction"] = "code"
    value = HTMLMotionComposition.model_validate(data)
    if change == "valid":
        validate(value, ctx)
    else:
        with pytest.raises(AuthError, match="MOTION_SCENE_COMPONENT_"):
            validate(value, ctx)


def test_photo_selection_is_bounded_distinct_and_legacy_request_stays_identical():
    base = dict(operation_id=uuid4(), source_asset_id=uuid4(), instruction="Fictício")
    assert "collection_photo_ids" not in MotionRequest(**base).model_dump()
    photo = uuid4()
    for selected in ((photo, photo), tuple(uuid4() for _ in range(5))):
        with pytest.raises(ValidationError):
            MotionRequest(**base, collection_photo_ids=selected)
    assert MotionRequest(**base, collection_photo_ids=(photo,)).collection_photo_ids == (photo,)
