"""Experimental lexical guard: it does not establish semantic truth."""

import re

from app.core.config import Settings


def creative_experiment_enabled(settings: Settings) -> bool:
    return settings.editorial_creative_experimental and settings.environment in {"development", "testing"}


# This bounded vocabulary is only an experimental guard, not a semantic verifier.
# Tokens outside it must come from the one confirmed fact cited by the model.
CREATIVE_STYLE_WORDS = frozenset(
    "a as o os um uma uns umas de da do das dos e em no na nos nas para pra por com "
    "que seu sua seus suas nosso nossa nossos nossas voce você teu tua te se aqui "
    "essa esse esta este isso uma neste nesta nesse nessa aquele aquela seus suas "
    "conheca conheça descubra descobrir mostrar mostre apresentar apresente compartilhar "
    "compartilhe conte contar vem venha ver veja olhar olhe imagine imaginar "
    "aproveite aproveitar convidamos convite conhecemos conhecer explorar explore "
    "mais perto perto momento momentos pausa pausas cuidado carinho detalhe detalhes "
    "historia história historias histórias sabor sabores experiencia experiência "
    "experiencias experiências seu jeito trabalho trabalho feito feita feito juntos "
    "junto dia dias pequena pequeno pequenos pequenas simples especial especiais "
    "destaque mostrar apresentar publico público clientes cliente gente conversa "
    "contato saber sobre compartilhar falar fale nós nos ao aos até ate tão tao "
    "whatsapp mensagem mensagens envie enviar peça peca chame chama mande pelo pela".split()
)
_CREATIVE_NEGATIONS = frozenset({"não", "nao", "sem", "nunca", "jamais", "nenhum", "nenhuma", "ninguém", "ninguem"})
_CREATIVE_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
_CREATIVE_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
_CREATIVE_QUANTITY = re.compile(
    r"(?i)(?:r\$\s*\d+(?:[.,]\d+)?|\b\d+(?:[.,]\d+)?\s*%|"
    r"\b\d+(?:[.,]\d+)?\s*(?:reais?|horas?|dias?|h)\b)"
)


def experimental_copy_matches_fact(copy: str, statement: str) -> bool:
    """Conservative lexical/provenance guard; human review remains mandatory."""
    text, evidence = copy.casefold(), statement.casefold()
    words = _CREATIVE_WORD.findall(text)
    if any(word in _CREATIVE_NEGATIONS for word in words):
        return False
    allowed = CREATIVE_STYLE_WORDS | frozenset(_CREATIVE_WORD.findall(evidence))
    if any(word not in allowed for word in words):
        return False
    numbers = set(_CREATIVE_NUMBER.findall(evidence))
    if any(number not in numbers for number in _CREATIVE_NUMBER.findall(text)):
        return False

    def compact(value: str) -> str:
        return re.sub(r"\s+", "", value)

    quantities = {compact(match.group()) for match in _CREATIVE_QUANTITY.finditer(evidence)}
    return all(compact(match.group()) in quantities for match in _CREATIVE_QUANTITY.finditer(text))
