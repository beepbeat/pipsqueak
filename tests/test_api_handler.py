import unittest
import asyncio
from aiounittest import async_test
from Modules.api_handler import *


class APIHandlerTest(unittest.TestCase):
    handler : BaseWebsocketAPIHandler

    def setUp(self):
        handler = BaseWebsocketAPIHandler(hostname="dev.api.fuelrats.com", tls=True)

    @async_test
    async def test_connect(self):
        if self.handler.connected: await self.handler.disconnect()
        await self.handler.connect()
        self.assertIsNotNone(self.handler.connected)

    @async_test
    async def test_disconnect(self):
        self.assertIsNotNone(self.handler.connected)
        await self.handler.disconnect()
        self.assertIsNone(self.handler.connected)

    def test_construct_request(self):
        self.assertEqual(
            self.handler.construct_request(("rescues", "search"), {"not":"this"}, {"key":"stuff"}),
            "{\"action\": [\"rescues\", \"search\"], \"meta\": {\"key\": \"stuff\"}, \"not\": \"this\"}"
        )
