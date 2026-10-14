import asyncio
import logging
from collections.abc import Awaitable, Callable

from curl_cffi.requests.exceptions import RequestException, Timeout
from pydantic import BaseModel

from app.domain.enums import Sport
from app.services.connection_manager import manager

logger = logging.getLogger(__name__)
POLL_INTERVAL = 15


async def poll_live[T: BaseModel](
    sport: Sport, fetch: Callable[[], Awaitable[list[T]]]
) -> None:
    previous: list[T] = []

    while True:
        try:
            current = await fetch()

            if current != previous:
                payload = [game.model_dump(mode="json") for game in current]
                await manager.broadcast(
                    {"type": "live_update", "sport": sport, "matches": payload}
                )
                previous = current

        # keep the logs clean
        except Timeout:
            logger.warning(
                "%s: timeout getting live matches, retry in %ds...",
                sport,
                POLL_INTERVAL,
            )

        except RequestException as e:
            logger.warning("%s: red/curl error polling: %s", sport, e)

        except Exception:
            logger.exception("%s: live poll failed, unexpected error", sport)

        await asyncio.sleep(POLL_INTERVAL)
