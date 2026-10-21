"""Independent, restartable SMTP worker for the native authentication outbox."""

import asyncio

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import Database
from app.services.auth_mail import deliver_once


async def main() -> None:
    configure_logging()
    settings = get_settings()
    db = Database(settings, auth=True)
    try:
        while True:
            if not await deliver_once(db, settings):
                await asyncio.sleep(1)
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
