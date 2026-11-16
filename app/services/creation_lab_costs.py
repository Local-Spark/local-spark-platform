"""Read-only accounting summaries; estimates are never represented as invoices."""

from sqlalchemy import bindparam, text


async def lab_costs(session, actor, runs=None):
    query = """SELECT r.id AS run_id,
      coalesce(sum(e.estimated_usd_micros),0) AS estimated_usd_micros,
      coalesce(sum(e.reserved_usd_micros) FILTER(WHERE e.estimated_usd_micros IS NULL),0)
        AS unpriced_reserved_usd_micros,
      count(e.id) FILTER(WHERE e.estimated_usd_micros IS NULL AND e.reserved_usd_micros>0)
        AS unpriced_calls
      FROM creation_lab_runs r LEFT JOIN creation_lab_effects e ON e.run_id=r.id
      WHERE r.actor_id=:actor AND r.origin='lab'"""
    params = {"actor": actor}
    if runs is not None:
        if not runs:
            return {}
        query += " AND r.id IN :runs"
        params["runs"] = runs
    statement = text(query + " GROUP BY r.id")
    if runs is not None:
        statement = statement.bindparams(bindparam("runs", expanding=True))
    rows = (await session.execute(statement, params)).mappings().all()
    return {
        row["run_id"]: {
            key: int(row[key]) for key in ("estimated_usd_micros", "unpriced_reserved_usd_micros", "unpriced_calls")
        }
        for row in rows
    }
