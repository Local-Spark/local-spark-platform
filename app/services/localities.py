"""Versioned IBGE snapshot: no external request or tenant data during onboarding."""

from functools import lru_cache
from pathlib import Path

from app.schemas.localities import CityRead, LocalitiesCatalog


@lru_cache(maxsize=1)
def catalog() -> LocalitiesCatalog:
    return LocalitiesCatalog.model_validate_json(
        (Path(__file__).parents[1] / "data" / "br-localities.json").read_text()
    )


@lru_cache(maxsize=27)
def cities_in_state(state_code: str) -> tuple[CityRead, ...]:
    return tuple(city for city in catalog().cities if city.state_code == state_code)


@lru_cache(maxsize=1)
def cities_by_code() -> dict[str, CityRead]:
    return {city.code: city for city in catalog().cities}
