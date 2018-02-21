import unittest
import asyncio
from Modules.api_handler import *


class APIHandlerTest(unittest.TestCase):
    handler = APIHandler(hostname="dev.api.fuelrats.com", tls=True)

    def test_connect(self):
        yield self.handler.connect()
        self.assertIsNotNone(self.handler._connection)

    def test_disconnect(self):
        self.assertIsNotNone(self.handler._connection)
        yield self.handler.disconnect()
        self.assertIsNone(self.handler._connection)

    def test_construct_request(self):
        self.assertEqual(
            self.handler.construct_request(("rescues", "search"), {"not":"this"}, {"key":"stuff"}),
            "{\"action\": [\"rescues\", \"search\"], \"meta\": {\"key\": \"stuff\"}, \"not\": \"this\"}"
        )
