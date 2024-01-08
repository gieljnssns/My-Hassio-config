"""View to accept incoming websocket connection."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Final

import aiohttp
from aiohttp import web
from flexmeasures_client.s2.cem import CEM
from flexmeasures_client.s2.control_types.FRBC.frbc_simple import FRBCSimple

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN, WS_VIEW_NAME, WS_VIEW_URI

_WS_LOGGER: Final = logging.getLogger(f"{__name__}.connection")


class WebsocketAPIView(HomeAssistantView):
    """View to serve a websockets endpoint."""

    name: str = WS_VIEW_NAME
    url: str = WS_VIEW_URI
    requires_auth: bool = False

    async def get(self, request: web.Request) -> web.WebSocketResponse:
        """Handle an incoming websocket connection."""

        return await WebSocketHandler(request.app["hass"], request).async_handle()


class WebSocketAdapter(logging.LoggerAdapter):
    """Add connection id to websocket messages."""

    def process(self, msg: str, kwargs: Any) -> tuple[str, Any]:
        """Add connid to websocket log messages."""
        if not self.extra or "connid" not in self.extra:
            return msg, kwargs
        return f'[{self.extra["connid"]}] {msg}', kwargs


class WebSocketHandler:
    """Handle an active websocket client connection."""

    cem: CEM

    def __init__(self, hass: HomeAssistant, request: web.Request) -> None:
        """Initialize an active connection."""
        self.hass = hass
        self.request = request
        self.wsock = web.WebSocketResponse(heartbeat=55)

        self.cem = CEM(fm_client=hass.data[DOMAIN]["fm_client"])
        frbc = FRBCSimple(**hass.data[DOMAIN]["frbc_config"])
        hass.data[DOMAIN]["cem"] = self.cem
        self.cem.register_control_type(frbc)

        self._logger = WebSocketAdapter(_WS_LOGGER, {"connid": id(self)})

        self._logger.debug("new websockets connection")

    async def _websocket_producer(self):
        """Send the messages available at the `cem` queue."""
        cem = self.cem

        while not cem.is_closed():
            message = await cem.get_message()

            self._logger.debug(message)

            await self.wsock.send_json(message)

    async def _websocket_consumer(self):
        """Process incoming messages."""
        cem = self.cem

        async for msg in self.wsock:
            message = msg.json()

            self._logger.debug(message)

            if msg.type == aiohttp.WSMsgType.TEXT:
                if msg.data == "close":
                    cem.close()
                    await self.wsock.close()
                else:
                    # process message
                    # breakpoint()
                    await cem.handle_message(message)

            elif msg.type == aiohttp.WSMsgType.ERROR:
                cem.close()

    async def async_handle(self) -> web.WebSocketResponse:
        """Handle a websocket response."""

        request = self.request
        wsock = self.wsock

        await wsock.prepare(request)

        # create "parallel" tasks for the message producer and consumer
        await asyncio.gather(
            self._websocket_consumer(),
            self._websocket_producer(),
        )

        return wsock
