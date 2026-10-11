"""CALMEAN HTTP client. Never log headers, response bodies or URLs with secrets."""
import asyncio
import aiohttp
from .const import API_URL
from .models import parse_devices, InvalidResponse

class InvalidAuth(Exception):
    """Token rejected."""

class CannotConnect(Exception):
    """Network, server or rate limit failure."""

class CalmeanClient:
    def __init__(self, session, token):
        self.session = session
        self.token = token

    async def devices(self):
        try:
            async with self.session.post(
                API_URL, headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=20), allow_redirects=False,
            ) as response:
                if response.status in (401, 403):
                    raise InvalidAuth("Token rejected")
                if response.status != 200:
                    raise CannotConnect("CALMEAN request failed")
                try:
                    payload = await response.json()
                except (ValueError, aiohttp.ContentTypeError) as exc:
                    raise InvalidResponse("Invalid JSON response") from exc
                return parse_devices(payload)
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            raise CannotConnect("CALMEAN unavailable") from exc
