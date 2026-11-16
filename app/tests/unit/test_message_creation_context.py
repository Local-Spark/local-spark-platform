"""Regressions for the institutional Café Aurora request (no paid providers)."""

from unittest.mock import AsyncMock

import pytest

from app.services.creation_lab_images import LabImageRequests
from app.services.message_creation_format import message_format


@pytest.mark.parametrize(
    ("message", "interpreted", "kind", "expected"),
    [
        (
            "Oi! Faz um post pro feed convidando o pessoal a conhecer o Café Aurora. Pode usar uma foto nossa que combine.",
            None,
            "text",
            "photo",
        ),
        ("Quero uma postagem para o feed", None, "text", "photo"),
        ("Não quero post pro feed", None, "text", None),
        ("Quero post pro feed e story", None, "text", None),
        ("Quero vídeo no feed", None, "text", None),
        ("Quero divulgar meu negócio", None, "text", None),
        ("Crie uma peça", None, "image", "photo"),
        ("Crie uma peça", None, "video", "reel"),
        ("Crie um story", "story", "text", "story"),
        ("Crie um vídeo", "short_video", "video", "reel"),
    ],
)
def test_format_does_not_silently_turn_text_into_story(message, interpreted, kind, expected):
    assert message_format(message, interpreted, kind) == expected


async def test_institutional_request_keeps_authorized_acervo_and_logo_without_offering():
    sources = [
        {"id": "logo", "role": "brand_logo"},
        {"id": "interior", "role": "space_photo", "version": 3, "sha256": "captured"},
    ]
    # These references were already authorized and fingerprinted by build_snapshot.
    session = AsyncMock()
    result = await LabImageRequests.resolve_sources(None, session, {}, {"sources": sources}, None)
    assert result == sources
    session.execute.assert_not_called()
