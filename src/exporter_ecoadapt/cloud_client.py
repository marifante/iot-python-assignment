"""
Class that handles sending the exported data to a server using websockets.
This class has inside an async method that can be used as a task to run periodically,
gathering data from a queue and sending it to the server.
"""
import asyncio
import websockets
import logging

log = logging.getLogger(__name__)


class WebSocketClient:
    def __init__(self, url: str, queue: asyncio.queues.Queue):
        """ Initialize the WebSocket client with the server URL.

        :param url: server URL
        :param queue: asyncio queue where the data that will be sent to the server is stored.
        """
        self.url = url
        self._queue = queue

    async def send_message(self, message: bytes):
        """Send a message to the WebSocket server.

        :param message: the message to send to the websocket server.
        """
        try:
            async with websockets.connect(self.url) as websocket:
                log.info(f"websocket = {websocket}")
                log.info(f"Sending {message} to the cloud server (type = {type(message)})")
                await websocket.send(message)
                response = await websocket.recv()
                log.info(f"Received from server: {response}")
        except Exception as e:
            log.error(f"WebSocket error: {e}")

    async def task(self):
        """ Async task that can be used to send the available data to the cloud server. """
        log.info(f"Starting cloud client task to send data to {self.url}")
        while True:
            data = await self._queue.get()
            await self.send_message(data)
