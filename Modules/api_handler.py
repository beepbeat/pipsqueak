"""
api_handler.py - Lets Mecha chat with the API.

Copyright (c) 2018 The Fuel Rats Mischief,
All rights reserved.

Licensed under the BSD 3-Clause License.

See LICENSE.md

This module is built on top of the Pydle system.

"""
import json
import asyncio
import logging
from typing import Union, Any, Mapping, MutableMapping, Dict, Set
from uuid import UUID, uuid4
from abc import abstractmethod

import websockets

import config

log = logging.getLogger(f'{config.Logging.base_logger}.api')


class APIError(Exception):
    """Raised when there is an error in the API or the handler itself."""
    pass


class BaseWebsocketAPIHandler(object):
    """Partly abstract base class for API Handlers."""
    api_version: str = None

    def __init__(self, hostname: str, token: str=None, tls=False):
        """
        Create a new API Handler. Connect immediately.

        Arguments:
             hostname (str): Hostname to connect to.
             token (str): OAuth token to be used for authorization or None if it's not needed.
             tls (bool): Whether to use TLS when connecting or not ('ws:' versus 'wss:').
        """
        self.hostname = hostname
        self.token = token
        self.tls = tls
        self._connection: websockets.WebSocketClientProtocol = None
        self._listener_task: asyncio.Task = None
        self._waiting_requests: Set[UUID] = set()
        self._request_responses: Dict[UUID, Mapping] = {}

    connected: bool = property(lambda self: self._connection is not None and self._connection.open)

    async def connect(self):
        """
        Connect to server, start the listener task and make sure we are on the correct API version.

        Raises:
            APIError: If this instance is already connected.
        """
        if self.connected:
            raise APIError(f"Already connected to a server: {self._connection.host}")

        uri = f"wss://{self.hostname}" if self.tls else f"ws://{self.hostname}"
        if self.token:
            uri += f"/?bearer={self.token}"

        self._connection = await websockets.connect(uri)

        # Grab the connect message and compare versions
        try:
            connect_message = json.loads(await self._connection.recv())
            if connect_message["meta"]["API-Version"] != self.api_version:
                raise APIError("Mismatched API and client versions!")
        except json.JSONDecodeError:
            raise APIError("Connect message from the API could not be parsed")
        except KeyError:
            log.error("Did not receive version field from API")

        self._listener_task = asyncio.get_event_loop().create_task(self._message_handler())

    async def disconnect(self):
        """
        Disconnect from the server.

        Raises:
            APIError: If this instance is not connected.
        """
        if not self.connected:
            raise APIError("Not connected to any server")

        self._listener_task.cancel()
        self._listener_task = None
        await self._connection.close()
        self._connection = None

    async def _message_handler(self):
        """
        Handler to be run continuously. Grabs messages from the connection, parses them and assigns them to the
        appropriate request.
        """
        while True:
            message = await self._connection.recv()
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                log.error(f"The following message from the API could not be parsed: {message}")
                continue

            try:
                request_id = UUID(data["meta"]["request_id"])
            except KeyError:
                log.error(f"Message from the API has no request id attached: {str(data)}")
                continue
            except ValueError:
                # not a valid UUID
                log.error(f"Request ID in API message was not a valid UUID: {data['meta']['request_id']}")
                continue

            if request_id not in self._waiting_requests:
                log.error(f"Received unexpected API response: {request_id}")
                continue
            else:
                self._request_responses[request_id] = data
                self._waiting_requests.remove(request_id)

    async def _send_raw(self, data: Union[str, bytes, dict]):
        """Send raw data to the server."""
        if not self.connected:
            raise APIError("Not connected to any server")

        if isinstance(data, str) or isinstance(data, bytes):
            await self._connection.send(data)
        else:
            await self._connection.send(json.dumps(data))

    async def request(self, data: MutableMapping[str, Any]) -> Mapping[str, Any]:
        """
        Make a request to the server, attaching a randomly generated UUID in order to identify and return the response.
        """
        request_id = uuid4()
        if "meta" in data.keys():
            data["meta"]["request_id"] = str(request_id)
        else:
            data["meta"] = {"request_id": str(request_id)}

        await self._send_raw(dict(data))
        self._waiting_requests.add(request_id)
        return await self._retrieve_response(request_id)

    async def _retrieve_response(self, request_id: UUID) -> Mapping[str, Any]:
        """Wait for a response to a particular request and return it."""
        if request_id not in self._waiting_requests:
            raise APIError("Cannot wait for response to a request that was never made")

        while request_id in self._waiting_requests:
            await asyncio.sleep(0.1)

        return self._request_responses[request_id]

    @abstractmethod
    async def update_rescue(self, rescue, full: bool) -> dict:
        """
        Send a rescue's data to the API.

        Arguments:
            rescue (Rescue): :class:`Rescue` object to be sent.
            full (bool): If this is True, all rescue data will be sent. Otherwise, only properties that have changed.
        """


class WebsocketAPIHandler21(BaseWebsocketAPIHandler):
    api_version = "v2.1"

    async def update_rescue(self, rescue, full: bool):
        """
        Send a rescue's data to the API.

        Arguments:
            rescue (Rescue): :class:`Rescue` object to be sent.
            full (bool): If this is True, all rescue data will be sent. Otherwise, only properties that have changed.
        """

        if not rescue.case_id:
            raise APIError("Cannot send rescue without ID to the API")

        request = {"action": ["rescues", "update"], "id": rescue.case_id, "data": rescue.json(full)}
        return await self.request(request)
