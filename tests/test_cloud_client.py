import asyncio
import pytest
from asynctest.mock import CoroutineMock
from asynctest import patch
from exporter_ecoadapt.cloud_client import WebSocketClient, format_websocket_url


@pytest.fixture
def queue():
    return asyncio.Queue()


@pytest.fixture
def websocket_client(queue):
    url = 'ws://example.com/websocket'
    return WebSocketClient(url, 8000, queue, "fake_subprotocol")


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
        mock_connect.assert_called_once_with(websocket_client._full_url, subprotocols=["fake_subprotocol"])
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
        mock_connect.assert_called_once_with(websocket_client._full_url, subprotocols=["fake_subprotocol"])
        mock_connect.return_value.__aenter__.return_value.send.assert_called_once_with(message)
        mock_connect.return_value.__aenter__.return_value.recv.assert_called_once()
        assert mock_connect.return_value.__aenter__.return_value.recv.return_value == b"Server response"


@pytest.mark.parametrize("url,port,expected", [
    # Good weather scenarios
    ("ws://example.com", 8080, "ws://example.com:8080"),
    ("wss://example.com", 8443, "wss://example.com:8443"),
    ("ws://192.168.1.1", 12345, "ws://192.168.1.1:12345"),
    ("wss://sub.domain.com", 443, "wss://sub.domain.com:443"),
    ("ws://example.com", 0, "ws://example.com:0"),
    ("wss://example.com", 65535, "wss://example.com:65535"),
])
def test_format_websocket_url_valid(url, port, expected):
    assert format_websocket_url(url, port) == expected

@pytest.mark.parametrize("url,port", [
    # Bad weather scenarios
    ("http://example.com", 8080),  # Invalid protocol
    ("ftp://example.com", 21),     # Invalid protocol
    ("wss://example.com", -1),     # Invalid port
    ("ws://example.com", 65536),   # Port out of range
    ("example.com", 8080),         # Missing protocol
    ("ws://", 8080),               # Missing domain
])
def test_format_websocket_url_invalid(url, port):
    with pytest.raises(ValueError):
        format_websocket_url(url, port)
