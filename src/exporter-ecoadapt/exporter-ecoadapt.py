#!/usr/bin/env python3
"""
A minimal EcoAdapt modbus reader
"""

import logging
import asyncio
import websockets
from pymodbus.client.sync import ModbusTcpClient as ModbusClient


# configure the client logging
log = logging.getLogger(__name__)


class EcoAdaptModbus:
    """ Class used to listen to EcoAdapt device and expose it's data through a queue. """

    def __init__(self, address: str, port: int, unit):
        """ Constructor of the the class who is in charge to gather data from EcoAdapt device.

        :param address: Modbus IP address.
        :param port: Modbus port.
        :param unit: Modbus unit.
        """
        self.address = address
        self.port = port
        self.unit = unit

    def run_sync_client(self):
        log.info("Setting up client")
        client = ModbusClient(self.address, port=self.port)
        client.connect()

        log.info("Reading registers")
        read_registers = [
            (0, 1),
            (1, 1),
            (2, 3),
            (244, 12),
            (352, 12),
            (388, 12),
            (424, 12),
        ]
        for r in read_registers:
            resp = client.read_input_registers(r[0], r[1], unit=self.unit)
            log.info("%s: %s: %s" % (r, resp, resp.registers))

        log.info("Closing client")
        client.close()


class WebSocketClient:
    def __init__(self, url: str):
        """ Initialize the WebSocket client with the server URL.

        :param url: server URL
        """
        self.url = url

    async def send_message(self, message: str):
        """Send a message to the WebSocket server.

        :param message: the message to send to the websocket server.
        """
        try:
            async with websockets.connect(self.url) as websocket:
                await websocket.send(message)
                response = await websocket.recv()
                log.info(f"Received from server: {response}")
        except Exception as e:
            log.error(f"WebSocket error: {e}")

    def send(self, message: str):
        """Run the async send_message method in an event loop.

        :param message: the message to send to the websocket server.
        """
        asyncio.run(self.send_message(message))



class EcoAd
#if __name__ == "__main__":
#    run_sync_client()
#
""""
Output when ran:
>> python3 ./src/exporter-ecoadapt/exporter-ecoadapt.py 
2021-03-19 12:31:18,597 MainThread      INFO     exporter-ecoadapt:23       Setting up client
2021-03-19 12:31:18,610 MainThread      INFO     exporter-ecoadapt:27       Reading registers
2021-03-19 12:31:18,615 MainThread      INFO     exporter-ecoadapt:39       (0, 1): ReadRegisterResponse (1): [514]
2021-03-19 12:31:18,622 MainThread      INFO     exporter-ecoadapt:39       (1, 1): ReadRegisterResponse (1): [2]
2021-03-19 12:31:18,635 MainThread      INFO     exporter-ecoadapt:39       (2, 3): ReadRegisterResponse (3): [30, 44285, 17639]
2021-03-19 12:31:18,643 MainThread      INFO     exporter-ecoadapt:39       (244, 12): ReadRegisterResponse (12): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
2021-03-19 12:31:18,646 MainThread      INFO     exporter-ecoadapt:39       (352, 12): ReadRegisterResponse (12): [49709, 17262, 20887, 15905, 45177, 15748, 0, 0, 0, 0, 0, 0]
2021-03-19 12:31:18,650 MainThread      INFO     exporter-ecoadapt:39       (388, 12): ReadRegisterResponse (12): [34030, 17262, 13400, 15907, 22707, 15748, 0, 0, 0, 0, 0, 0]
2021-03-19 12:31:18,654 MainThread      INFO     exporter-ecoadapt:39       (424, 12): ReadRegisterResponse (12): [54339, 16973, 54339, 16973, 43051, 16949, 0, 0, 0, 0, 0, 0]
2021-03-19 12:31:18,655 MainThread      INFO     exporter-ecoadapt:41       Closing client
"""
