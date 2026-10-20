"""Bounded readiness probe for local/CI Temporal, without paid integrations."""

import asyncio
import os

from temporalio.client import Client


async def main():
    for attempt in range(30):
        try:
            client = await Client.connect(os.environ.get("TEST_TEMPORAL_ADDRESS", "localhost:7233"))
            if await client.service_client.check_health():
                return
        except Exception:
            if attempt == 29:
                raise
        await asyncio.sleep(1)
    raise SystemExit("Temporal did not become healthy")


if __name__ == "__main__":
    asyncio.run(main())
