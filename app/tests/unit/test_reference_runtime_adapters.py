"""Explicit runtime opt-in still uses a transport fixture in these tests."""

from dataclasses import replace
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.adapters.jev_reference_recommendations import (
    JevReferenceRecommendations,
    RecommendationCandidate,
    RecommendationError,
    RecommendationInput,
)
from app.adapters.jev_reference_similarity_levels import JevReferenceSimilarityLevels
from app.tests.unit.test_jev_reference_recommendations import Guard, answer
from app.tests.unit.test_jev_reference_similarity_levels import body, data


async def test_recommendation_can_resume_from_own_similarity_without_google_names(monkeypatch):
    candidate = RecommendationCandidate(uuid4(), None, (), Decimal("8.1"), "high")
    source = RecommendationInput(("Café",), None, (candidate,))
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json=answer(["candidate_0"], 1)))
    monkeypatch.setattr(httpx, "AsyncHTTPTransport", lambda **_: transport)
    adapter = JevReferenceRecommendations(SecretStr("fake"), "test-model", Guard(), enabled=True, network_enabled=True)
    result = await adapter.recommend(source, uuid4())
    assert result[0].candidate_id == candidate.candidate_id
    with pytest.raises(RecommendationError, match="RECOMMENDATION_INPUT_INVALID"):
        await adapter.recommend(replace(source, candidates=(replace(candidate, similarity_level="unknown"),)), uuid4())


async def test_similarity_network_optin_constructs_nonretrying_transport_fixture(monkeypatch):
    value = data()
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json=body()))
    monkeypatch.setattr(httpx, "AsyncHTTPTransport", lambda **_: transport)
    result = await JevReferenceSimilarityLevels(
        SecretStr("fake"), "test-model", Guard(), enabled=True, network_enabled=True
    ).classify(value, uuid4())
    assert result.judgments[0].similarity_level == "high"
