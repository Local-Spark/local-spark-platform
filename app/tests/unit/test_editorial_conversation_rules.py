"""Deterministic text rules abstain when a claim is incomplete."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.editorial_conversation import classify


def test_price_and_availability_rules() -> None:
    now = datetime(2026, 10, 23, 12, tzinfo=ZoneInfo("America/Sao_Paulo"))
    assert classify("Hoje o X-tudo está 20 reais", now)[0] == "price"
    kind, proposal, reply = classify("O X-tudo está R$ 20,50 hoje", now)
    assert (kind, proposal["summary"], proposal["valid_until"]) == ("price", "X-tudo: R$ 20,50 hoje", "2026-10-23")
    assert "Confirmar" in reply
    assert classify("Hoje o X-tudo está 0 reais", now)[0] == "unknown"
    assert classify("O X-tudo está 20 reais", now)[0] == "unknown"
    assert classify("Hoje tenho agenda livre às 15h", now)[1]["summary"] == "Horário livre hoje às 15:00"
    assert classify("Hoje tenho horário livre as 15:30", now)[1]["summary"] == "Horário livre hoje às 15:30"
    assert classify("Hoje tenho horário livre as 25h", now)[0] == "unknown"
    assert classify("Hoje tenho horário livre as 15:99", now)[0] == "unknown"
    assert classify("Qual é a melhor hora para postar?", now)[0] == "unknown"
