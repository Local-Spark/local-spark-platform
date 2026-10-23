"""The local decision baseline and claim guard fail closed on unsupported claims."""

from uuid import uuid4

from cryptography.fernet import Fernet
from pydantic import SecretStr

from app.schemas.editorial_proposals import ProposalDraft
from app.services.editorial_proposals import EditorialProposalService


def _data(kind=None, facts=None, topics=None):
    return {
        "confirmed_facts": facts or [],
        "preferences": {"avoided_topics": topics or []},
        "material": "foto",
        "material_kind": kind,
        "context_version": 0,
    }


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
    assert not service._safe(good, _data("image", facts), set())
    assert not service._safe(good.model_copy(update={"angle": "Combo por R$ 99"}), _data("image", facts), {fact_id})
    assert not service._safe(
        good.model_copy(update={"title": "Política do combo"}), _data("image", facts, ["política"]), {fact_id}
    )


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
