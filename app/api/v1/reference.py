from typing import Annotated

from fastapi import APIRouter, Path

from app.schemas.localities import CityRead, StateRead
from app.services.localities import catalog, cities_in_state

reference_router = APIRouter(prefix="/api/v1/reference", tags=["reference"])


@reference_router.get("/states", response_model=list[StateRead])
async def states() -> list[StateRead]:
    return catalog().states


@reference_router.get("/cities/{state_code}", response_model=list[CityRead])
async def cities(state_code: Annotated[str, Path(pattern=r"^[A-Z]{2}$")]) -> tuple[CityRead, ...]:
    return cities_in_state(state_code)
