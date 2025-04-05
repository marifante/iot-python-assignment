import asyncio
import pytest
from asynctest.mock import CoroutineMock
from asynctest import patch
from exporter_ecoadapt.cloud_client import WebSocketClient


@pytest.fixture
def queue():
    return asyncio.Queue()


@pytest.fixture
def websocket_client(queue):
    url = 'ws://example.com/websocket'
    return WebSocketClient(url, queue)


@pytest.mark.asyncio
async def test_send_message_good_weather(websocket_client):
    """ Test sending a message in a good weather scenario (no error shown). """
    # Arrange: create message to be sent and mock websocket client methods.
    # The mock here is a bit tricky (https://github.com/pytest-dev/pytest-asyncio/issues/794)
    # because if we directly use an AsyncMock with async context managers it doesn't work.
    # The way to use it is to set an AsyncMock as the return value of __aenter__ (context manager async enter magic method).
    message = b"Test message"

    with patch('websockets.connect') as mock_connect:
        async def mock_aenter(_):
            mock_connect.return_value.__aenter__.return_value = CoroutineMock()

        async def mock_aexit(obj, exc_type, exc, tb):
            return

        mock_connect.__aexit__ = mock_aexit
        mock_connect.__aenter__ = mock_aenter

        mock_connect.return_value.__aenter__.return_value.send = CoroutineMock()
        mock_connect.return_value.__aenter__.return_value.recv = CoroutineMock(return_value=b"Server response")

        # Act: send the message to the server
        await websocket_client.send_message(message)

        # Assert: check if the expected calls occurred
        mock_connect.assert_called_once_with(websocket_client.url)
        mock_connect.return_value.__aenter__.return_value.send.assert_called_once_with(message)
        mock_connect.return_value.__aenter__.return_value.recv.assert_called_once()
        assert mock_connect.return_value.__aenter__.return_value.recv.return_value == b"Server response"



@pytest.mark.asyncio
async def test_task_good_weather(websocket_client, queue):
    """ Test a good weather scenario with the task used to read data from the
    queue and send it to the server. """
    # Arrange: put message in the queue and mock websocket-related things.
    message = b"Test message number 2"
    await queue.put(message)

    with patch('websockets.connect') as mock_connect:
        async def mock_aenter(_):
            mock_connect.return_value.__aenter__.return_value = CoroutineMock()

        async def mock_aexit(obj, exc_type, exc, tb):
            return

        mock_connect.__aexit__ = mock_aexit
        mock_connect.__aenter__ = mock_aenter

        mock_connect.return_value.__aenter__.return_value.send = CoroutineMock()
        mock_connect.return_value.__aenter__.return_value.recv = CoroutineMock(return_value=b"Server response")

        task = asyncio.create_task(websocket_client.task())

        # Act: Run the task for a short period and then cancel it.
        await asyncio.sleep(0.1)
        task.cancel()

        # Assert: check that the message was sent to the server.
        mock_connect.assert_called_once_with(websocket_client.url)
        mock_connect.return_value.__aenter__.return_value.send.assert_called_once_with(message)
        mock_connect.return_value.__aenter__.return_value.recv.assert_called_once()
        assert mock_connect.return_value.__aenter__.return_value.recv.return_value == b"Server response"


