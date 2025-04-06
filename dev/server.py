###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) Crossbar.io Technologies GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

#
# A local webserver to receive message sent by exporter. For dev and debugging only!
#

import logging
import asyncio
import argparse

from autobahn.asyncio.websocket import WebSocketServerProtocol, WebSocketServerFactory
import power_elec6_message_pb2 as protobuf


FORMAT = (
    "%(asctime)-15s %(threadName)-15s "
    "%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
)

logging.basicConfig(format=FORMAT, level=logging.INFO)

log = logging.getLogger(__name__)


EXPORTER_ECODATA_PROTOBUF_V1 = "exporter_ecodata_protobuf_v1"


def decode_protobuf_v1(payload: bytes):
    """ Decode a protobuf v1 payload.

    :param payload: the binary payload to be decoded.
    """
    protobuf_msg = protobuf.PowerElec6Message()
    protobuf_msg.ParseFromString(payload)

    msg2print = "CLOUD SERVER RECEIVED DATA = \n"
    msg2print += f"SOFTWARE_VERSION = {protobuf_msg.software_version}, "
    msg2print += f"MODBUS_TABLE_VERSION = {protobuf_msg.modbus_table_version}, "
    msg2print += f"MAC_ADDRESS = {protobuf_msg.mac_address}\n"

    for idx, ci in enumerate(protobuf_msg.circuits_info):
        msg2print += f"({ci.connector:2}, {ci.channel:2}, 0x{ci.configuration:04X}, {ci.rms_voltage:12.8f} V, {ci.frequency:12.8f} Hz)"
        msg2print += "\n" if (idx + 1) % 3 == 0 else ", "

    return msg2print


class MyServerProtocol(WebSocketServerProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._supported_subprotocols = [EXPORTER_ECODATA_PROTOBUF_V1]
        self._last_negotiated_subproto = ""
        self._received_data = list()

    def onConnect(self, request):
        """ Handle that will be called when a client tries to connect to the websocket server.

        Here the client inform us about the requested subprotocol to communicate and we
        check if that subprotocol is supported.
        """
        log.info(f"Client connecting: {request.peer}")
        self._last_negotiated_subproto = ""

        # Check if the client requested any supported subprotocols
        if request.protocols:
            log.info(f"Client requested subprotocols: {request.protocols}")
            for protocol in request.protocols:
                if protocol in self._supported_subprotocols:
                    log.info(f"Agreeing to subprotocol: {protocol}")
                    self._last_negotiated_subproto = protocol
                    break

        return self._last_negotiated_subproto

    async def onOpen(self):
        log.info("WebSocket connection open.")

    def onMessage(self, payload, isBinary):
        """ Handle called when the server receives a message from the client. """

        if self._last_negotiated_subproto == EXPORTER_ECODATA_PROTOBUF_V1:
            if not isBinary:
                log.error(f"Received a '{EXPORTER_ECODATA_PROTOBUF_V1}' message, but is not binary, this is wrong.")
            else:
                decoded_data = decode_protobuf_v1(payload)
                self.sendMessage(b"OK", isBinary=True)
                self._received_data.append(decoded_data)
        else:
            log.warning(f"Subprotocol {self._last_negotiated_subproto} data decoding is not implemented, doing nothing...")

    def onClose(self, wasClean, code, reason):
        log.info(f"WebSocket connection closed (reason = {0}). Received data in this connection: ".format(reason))
        for msg in self._received_data:
            log.info(msg)

        self._received_data = list()


def parse_args():
    """ Parse arguments given to this CLI. """
    parser = argparse.ArgumentParser(description="A local websocket server that receives and prints messages")
    parser.add_argument("--port", "-p", help="Port to serve (default 9000)", type=int, default=9000)
    parser.add_argument("--addr", "-a", help="IP address to mount the serverPort to serve", type=str, required=True)

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    server_url = f"ws://{args.addr}:{args.port}"
    log.info(f"Starting server on {server_url}")
    factory = WebSocketServerFactory(server_url)
    factory.protocol = MyServerProtocol

    loop = asyncio.get_event_loop()
    coro = loop.create_server(factory, "0.0.0.0", args.port)
    server = loop.run_until_complete(coro)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        log.warning("Interrupted! Closing server.")
    finally:
        server.close()
        loop.close()
