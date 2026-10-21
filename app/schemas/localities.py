from pydantic import BaseModel


class StateRead(BaseModel):
    code: str
    name: str


class CityRead(BaseModel):
    code: str
    name: str
    state_code: str


class LocalitiesCatalog(BaseModel):
    source: str
    retrieved_at: str
    states: list[StateRead]
    cities: list[CityRead]
