"""The local decision baseline and claim guard fail closed on unsupported claims."""

from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr

from app.schemas.editorial_proposals import ProposalDraft, ScriptEdit, ScriptScene
from app.services.editorial_proposals import EditorialProposalService, _has_unconfirmed_claim


def _data(kind=None, facts=None, topics=None):
    return {
        "confirmed_facts": facts or [],
        "preferences": {"avoided_topics": topics or []},
        "material": "foto",
        "material_kind": kind,
        "context_version": 0,
    }


def test_script_edit_requires_factual_scene_and_rejects_new_commercial_claims():
    fact_id = uuid4()
    fact = ScriptScene(
        role="fact",
        visual="brand_card",
        on_screen_text="X-tudo por R$ 20.",
        voiceover="X-tudo por R$ 20.",
        fact_ids=[fact_id],
    )
    cta = ScriptScene(
        role="cta",
        visual="brand_card",
        on_screen_text="Fale conosco",
        voiceover="Chame a gente.",
        fact_ids=[],
    )
    edit = ScriptEdit(
        operation_id=uuid4(),
        expected_version=1,
        title="Conheça nosso X-tudo",
        angle="Mostre o lanche aos clientes.",
        script=[fact, cta],
    )
    assert not _has_unconfirmed_claim(edit, "X-tudo por R$ 20.")
    assert not _has_unconfirmed_claim(edit.model_copy(update={"title": "X-tudo por R$ 20"}), "X-tudo por R$ 20.")
    assert _has_unconfirmed_claim(edit.model_copy(update={"title": "Hoje tem X-tudo por R$ 10"}), "X-tudo por R$ 20.")
    with pytest.raises(ValueError, match="exactly one fact"):
        ScriptEdit(operation_id=uuid4(), expected_version=1, title=edit.title, angle=edit.angle, script=[cta, cta])


def test_baseline_formats_and_claim_guard(settings, fake_database):
    service = EditorialProposalService(settings, fake_database)
    fact_id = uuid4()
    facts = [{"id": str(fact_id), "statement": "Combo por R$ 20", "kind": "offer"}]
    assert service._baseline(_data("audio")).format == "short_video"
    assert service._baseline(_data("video")).format == "short_video"
    assert service._baseline(_data("image")).format == "photo"
    assert service._baseline(_data("text", facts)).fact_ids == [fact_id]
    good = ProposalDraft(
        title="Mostre o combo",
        format="photo",
        angle="Apresente o combo por R$ 20.",
        fact_ids=[fact_id],
        hypotheses=[],
        questions=[],
    )
    assert service._safe(good, _data("image", facts), {fact_id})
    assert not service._safe(good.model_copy(update={"fact_ids": []}), _data("image", facts), {fact_id})
    assert not service._safe(good, _data("image", facts), set())
    assert not service._safe(good.model_copy(update={"angle": "Combo por R$ 99"}), _data("image", facts), {fact_id})
    assert not service._safe(
        good.model_copy(update={"title": "Política do combo"}), _data("image", facts, ["política"]), {fact_id}
    )
    assert not service._safe(
        good,
        _data("image", [{"id": str(fact_id), "statement": "Política de preços", "kind": "offer"}], ["política"]),
        {fact_id},
    )
    grounded = service._ground(
        good.model_copy(update={"title": "Promoção incrível", "angle": "Corra antes de acabar"}),
        _data("image", facts),
    )
    assert grounded.title == "Uma história do seu negócio"
    assert grounded.angle == "Apresente este ponto do negócio: Combo por R$ 20."
    assert grounded.fact_ids == [fact_id]
    assert grounded.format == "photo"


def test_private_source_requires_valid_ciphertext(settings, fake_database):
    key = Fernet.generate_key().decode()
    configured = settings.model_copy(update={"meta_encryption_key": SecretStr(key)})
    service = EditorialProposalService(configured, fake_database)
    encrypted = Fernet(key.encode()).encrypt(b"Mensagem do dono").decode()
    assert service._source({"ciphertext": encrypted, "transcript_ciphertext": None}) == "Mensagem do dono"
    assert service._source({"ciphertext": "bad", "transcript_ciphertext": None}) is None
    assert service._source({"ciphertext": None, "transcript_ciphertext": None}) is None
    without_key = EditorialProposalService(settings, fake_database)
    assert without_key._source({"ciphertext": encrypted, "transcript_ciphertext": None}) is None


def test_storyboard_uses_only_confirmed_fact_and_authorized_material(settings, fake_database):
    service = EditorialProposalService(settings, fake_database)
    fact_id, asset_id = uuid4(), uuid4()
    data = _data("image", [{"id": str(fact_id), "statement": "X-tudo por R$ 20", "kind": "price"}])
    data["source_asset_id"] = asset_id
    baseline = service._baseline(data)
    assert [scene.role for scene in baseline.script] == ["material", "fact", "cta"]
    assert baseline.script[0].source_asset_id == asset_id
    assert baseline.script[0].fact_ids == []
    assert baseline.script[1].on_screen_text == "X-tudo por R$ 20."
    assert baseline.script[1].fact_ids == [fact_id]
    assert baseline.script[2].voiceover == "Entre em contato para saber mais."
    assert baseline.script[2].fact_ids == []
    assert all("foto" not in scene.on_screen_text.casefold() for scene in baseline.script)

    proposed = baseline.model_copy(update={"scene_plan": ["cta", "cta", "material"]})
    grounded = service._ground(proposed, data)
    assert [scene.role for scene in grounded.script] == ["fact", "cta", "material"]
    assert grounded.script[0].fact_ids == [fact_id]
    assert grounded.script[2].source_asset_id == asset_id


def test_storyboard_omits_visual_scene_without_image_or_fact(settings, fake_database):
    service = EditorialProposalService(settings, fake_database)
    fact_id, asset_id = uuid4(), uuid4()
    data = _data("audio", [{"id": str(fact_id), "statement": "Atendimento às 15h", "kind": "hours"}])
    data["source_asset_id"] = asset_id
    draft = service._baseline(data)
    assert [scene.role for scene in draft.script] == ["fact", "cta"]
    assert all(scene.source_asset_id is None for scene in draft.script)
    assert service._script(draft.model_copy(update={"scene_plan": ["material"]}), data)[0].role == "fact"
    assert service._baseline(_data("image")).script == []
