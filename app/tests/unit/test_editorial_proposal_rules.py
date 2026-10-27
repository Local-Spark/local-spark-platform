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


def test_experimental_copy_is_tied_to_one_confirmed_fact(settings, fake_database):
    service = EditorialProposalService(settings, fake_database)
    wrong_id, selected_id, asset_id = uuid4(), uuid4(), uuid4()
    data = _data(
        "image",
        [
            {"id": str(wrong_id), "statement": "Bolo por R$ 30", "kind": "price"},
            {"id": str(selected_id), "statement": "Croissant por R$ 20", "kind": "price"},
        ],
    )
    data["source_asset_id"] = asset_id
    draft = ProposalDraft(
        title="Sua pausa com croissant",
        format="photo",
        angle="Conheça croissant por R$ 20",
        fact_ids=[selected_id],
        hypotheses=[],
        questions=[],
        scene_plan=["material", "fact", "cta"],
    )
    assert service._safe_experimental(draft, data, {wrong_id, selected_id})
    result = service._ground(draft, data, experimental=True)
    assert result.title == draft.title and result.angle == draft.angle
    assert result.fact_ids == [selected_id]
    assert result.script[0].on_screen_text == draft.title
    assert result.script[0].voiceover == draft.angle
    assert result.script[0].source_asset_id == asset_id
    assert result.script[1].on_screen_text == "Croissant por R$ 20."
    assert result.script[1].voiceover == "Croissant por R$ 20."
    assert result.script[1].fact_ids == [selected_id]
    assert result.script[2].on_screen_text == "Fale com o negócio"
    assert result.script[2].voiceover == "Entre em contato para saber mais."
    assert not service._safe_experimental(draft.model_copy(update={"fact_ids": []}), data, {selected_id})
    assert not service._safe_experimental(
        draft.model_copy(update={"fact_ids": [selected_id, wrong_id]}), data, {selected_id, wrong_id}
    )
    assert not service._safe_experimental(draft, data, {wrong_id})
    assert not service._safe_experimental(draft, _data("image", [data["confirmed_facts"][0]]), {selected_id})
    assert not service._safe_experimental(draft, _data("image", data["confirmed_facts"], ["croissant"]), {selected_id})
    # Preserve baseline guard: the first fact's avoided topic blocks the draft too.
    assert not service._safe_experimental(draft, _data("image", data["confirmed_facts"], ["bolo"]), {selected_id})


@pytest.mark.parametrize(
    "title,angle,statement",
    [
        ("Croissant vegano", "Conheça croissant por R$ 20", "Croissant por R$ 20"),
        ("Croissant garantido", "Conheça croissant por R$ 20", "Croissant por R$ 20"),
        ("O melhor croissant", "Conheça croissant por R$ 20", "Croissant por R$ 20"),
        ("Croissant sem açúcar", "Conheça croissant", "Croissant por R$ 20"),
        ("Croissant por R$ 30", "Conheça croissant", "Croissant por R$ 20"),
        ("Promoção de 20%", "Conheça a promoção", "Promoção 20 reais"),
        ("Desconto de 20%", "Conheça o desconto", "Desconto por R$ 20"),
        ("Atendimento por 15 dias", "Conheça o atendimento", "Atendimento às 15h"),
    ],
)
def test_experimental_copy_abstains_from_unsupported_claims(settings, fake_database, title, angle, statement):
    service = EditorialProposalService(settings, fake_database)
    fact_id = uuid4()
    data = _data("image", [{"id": str(fact_id), "statement": statement, "kind": "product"}])
    draft = ProposalDraft(title=title, format="photo", angle=angle, fact_ids=[fact_id], hypotheses=[], questions=[])
    assert not service._safe_experimental(draft, data, {fact_id})


def test_experimental_copy_rejects_another_facts_numbers_and_never_alters_factual_text(settings, fake_database):
    service = EditorialProposalService(settings, fake_database)
    a, b = uuid4(), uuid4()
    data = _data(
        "text",
        [
            {"id": str(a), "statement": "Croissant por R$ 20", "kind": "product"},
            {"id": str(b), "statement": "Bolo por R$ 30", "kind": "product"},
        ],
    )
    draft = ProposalDraft(
        title="Croissant por R$ 30",
        format="story",
        angle="Conheça croissant",
        fact_ids=[a],
        hypotheses=[],
        questions=[],
    )
    assert not service._safe_experimental(draft, data, {a, b})
    assert service._ground(draft, data).title == "Uma história do seu negócio"


def test_experimental_flag_defaults_off_and_cannot_be_enabled_in_production(settings):
    assert not settings.editorial_creative_experimental
    for environment in ("production", "staging"):
        forbidden = settings.model_copy(update={"environment": environment, "editorial_creative_experimental": True})
        with pytest.raises(ValueError, match="restricted to development and testing"):
            forbidden.editorial_ai_safety()
    allowed = settings.model_copy(update={"environment": "testing", "editorial_creative_experimental": True})
    assert allowed.editorial_ai_safety() is allowed


def test_experimental_script_fails_closed_and_bounds_voiceover(settings, fake_database):
    service = EditorialProposalService(settings, fake_database)
    fact_id = uuid4()
    data = _data("image", [{"id": str(fact_id), "statement": "Croissant por R$ 20", "kind": "price"}])
    data["source_asset_id"] = uuid4()
    draft = ProposalDraft(
        title="Conheça croissant",
        angle="Conheça " * 35,
        format="photo",
        fact_ids=[fact_id],
        hypotheses=[],
        questions=[],
        scene_plan=["material", "fact", "cta"],
    )
    assert service._script(draft, data, experimental=True)[0].voiceover == draft.title
    with pytest.raises(ValueError, match="fact source unavailable"):
        service._script(draft.model_copy(update={"fact_ids": [uuid4()]}), data, experimental=True)
    with pytest.raises(ValueError, match="fact source unavailable"):
        service._script(draft.model_copy(update={"fact_ids": []}), data, experimental=True)


def test_experimental_rejects_id_missing_from_loaded_fact_snapshot(settings, fake_database):
    service = EditorialProposalService(settings, fake_database)
    actual_id, stale_id = uuid4(), uuid4()
    data = _data("image", [{"id": str(actual_id), "statement": "Croissant artesanal", "kind": "product"}])
    draft = ProposalDraft(
        title="Conheça croissant",
        format="photo",
        angle="Conheça nosso croissant artesanal",
        fact_ids=[stale_id],
        hypotheses=[],
        questions=[],
    )
    # Model-provided ID passes the initial ID set but is absent from the snapshot.
    assert service._safe(draft, data, {stale_id})
    assert not service._safe_experimental(draft, data, {stale_id})
