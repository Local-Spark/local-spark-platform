"""Refresh the reviewed IBGE snapshot outside the request path; review the diff before release."""

import gzip
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import urlopen

SOURCE = "https://servicodados.ibge.gov.br/api/v1/localidades"


def fetch(resource):
    with urlopen(f"{SOURCE}/{resource}?orderBy=nome", timeout=30) as response:
        raw = response.read()
    return json.loads(gzip.decompress(raw) if raw.startswith(b"\x1f\x8b") else raw)


def main():
    states = [{"code": row["sigla"], "name": row["nome"]} for row in fetch("estados")]
    cities = [
        {
            "code": str(row["id"]),
            "name": row["nome"],
            "state_code": row["regiao-imediata"]["regiao-intermediaria"]["UF"]["sigla"],
        }
        for row in fetch("municipios")
    ]
    if len(states) != 27 or len(cities) < 5500 or len({row["code"] for row in cities}) != len(cities):
        raise SystemExit("Unexpected IBGE catalog; existing snapshot preserved")
    result = {
        "source": SOURCE,
        "retrieved_at": datetime.now(UTC).date().isoformat(),
        "states": states,
        "cities": cities,
    }
    target = Path(__file__).resolve().parents[1] / "app" / "data" / "br-localities.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    print(
        f"Snapshot refreshed: {len(states)} states, {len(cities)} municipalities. Review data and tests before release."
    )


if __name__ == "__main__":
    main()
