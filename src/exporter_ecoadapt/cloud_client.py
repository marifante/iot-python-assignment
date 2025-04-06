"""
Class that handles sending the exported data to a server using websockets.
This class has inside an async method that can be used as a task to run periodically,
gathering data from a queue and sending it to the server.
"""
import asyncio
import websockets
import logging
import re


log = logging.getLogger(__name__)


def format_websocket_url(url: str, port: int) -> str:
    """ Format an url string and a port number into a valid websocket url.

    :param url: server URL (it should contain the protocol (ws or wss) and the IP address).
    :param port: server port.
    """
    if (port < 0) or (port > 65535):
        raise ValueError(f"Port number {port} is invalid!")

    full_url = f"{url}:{port}"

    websocket_url_regex = re.compile(
        r'^(ws|wss)://'  # Protocol (ws or wss)
        r'([a-zA-Z0-9.-]+)'  # Domain name or IP address
        r'(:[0-9]{1,5})?'  # Optional port number
        r'(/.*)?$'  # Optional path
    )
    if not  re.match(websocket_url_regex, url):
        raise ValueError(f"The combination {url} & {port} is not a valid for a websocket")

    return full_url


class WebSocketClient:
    def __init__(self, url: str, port: int, queue: asyncio.queues.Queue, subprotocol: str):
        """ Initialize the WebSocket client with the server URL.

        :param url: server URL (it should contain the protocol (ws or wss) and the IP address).
        :param port: server port.
        :param queue: asyncio queue where the data that will be sent to the server is stored.
        :param subprotocol: subprotocol used to communicate with the cloud server.
        """
        self._url = url
        self._port = port

        self._full_url = format_websocket_url(self._url, self._port)

        self._queue = queue
        self.subprotocol = [subprotocol]

    async def send_message(self, message: bytes):
        """Send a message to the WebSocket server.

        :param message: the message to send to the websocket server.
        """
        try:
            async with websockets.connect(self._full_url, subprotocols=self.subprotocol) as websocket:
                log.info(f"Sending {message} to the cloud server (type = {type(message)})")
                await websocket.send(message)
                response = await websocket.recv()
                log.info(f"Received from server: {response}")
        except Exception as e:
            log.error(f"WebSocket error: {e}")

    async def task(self):
        """ Async task that can be used to send the available data to the cloud server. """
        log.info(f"Starting cloud client task to send data to {self._full_url}")
        while True:
            data = await self._queue.get()
            await self.send_message(data)
