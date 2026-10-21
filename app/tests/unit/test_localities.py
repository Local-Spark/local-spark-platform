import pytest
from pydantic import ValidationError

from app.schemas.onboarding import OnboardingCreate
from app.services.localities import catalog, cities_by_code, cities_in_state


def payload(**changes):
    return {
        "name": "Studio da Ana",
        "category": "Manicure e pedicure",
        "city": "São Paulo",
        "state_code": "SP",
        "city_ibge_code": "3550308",
        "description": "Unhas e cuidados",
        "phone": "+5511999999999",
        "brand_color": "#12abEF",
        "accept_terms": True,
        "accept_privacy": True,
        **changes,
    }


def test_reference_endpoints_use_complete_versioned_official_data(client):
    data = catalog()
    states = client.get("/api/v1/reference/states")
    assert states.status_code == 200 and len(states.json()) == 27
    assert len(data.cities) == len(cities_by_code()) == 5571
    assert {city.state_code for city in data.cities} == {state.code for state in data.states}
    assert cities_by_code()["5101837"].name == "Boa Esperança do Norte"
    cities = client.get("/api/v1/reference/cities/SP")
    assert cities.status_code == 200 and len(cities.json()) == 645
    assert {row["state_code"] for row in cities.json()} == {"SP"}
    assert client.get("/api/v1/reference/cities/ZZ").json() == []
    assert client.get("/api/v1/reference/cities/sp").status_code == 422
    assert cities_in_state("SP") is cities_in_state("SP")
    assert catalog() is data


def test_structured_city_and_custom_activity_and_color():
    value = OnboardingCreate(**payload(category="Conserto de instrumentos musicais"))
    assert value.state_code == "SP" and value.city_ibge_code == "3550308"
    assert value.brand_color == "#12abEF"


@pytest.mark.parametrize(
    "changes",
    [
        {"city_ibge_code": None},
        {"state_code": None},
        {"city_ibge_code": "9999999"},
        {"state_code": "RJ"},
        {"city": "Santo André"},
        {"city_ibge_code": "355030"},
        {"state_code": "sp"},
        {"state_code": "ZZ"},
        {"brand_color": "red"},
        {"brand_color": "#abc"},
        {"category": "  "},
    ],
)
def test_locality_mismatch_and_invalid_profile_are_rejected(changes):
    with pytest.raises(ValidationError):
        OnboardingCreate(**payload(**changes))
