#!/usr/bin/env python3
"""
A minimal EcoAdapt modbus reader
"""

import logging
import asyncio
import websockets
from enum import Enum
from collections import namedtuple
from pymodbus.client.async_tcp import AsyncModbusTcpClient as ModbusClient


# configure the client logging
log = logging.getLogger(__name__)


EcoElec6CircuitInfo = namedtuple("EcoElec6CircuitInfo", ["connector", "channel", "param", "value"])


class EcoElec6Register(Enum):
    """ Enum with the offset (first element) and length (second element) of 
    each data register of EcoElec6 device. """
    # General information
    SOFTWARE_VERSION              = (0, 1)
    MODBUS_TABLE_VERSION          = (1, 1)
    MAC_ADDRESS                   = (2, 3)

    # Information per circuit
    CIRCUIT_CONFIGURATION         = (8,   18)
    ACTIVE_ENERGY_IMPORT_INDEX    = (28,  18)
    REACTIVE_ENERGY_IMPORT_INDEX  = (64,  18)
    ACTIVE_ENERGY_EXPORT_INDEX    = (100, 18)
    REACTIVE_ENERGY_EXPORT_INDEX  = (136, 18)
    ACTIVE_POWER                  = (172, 18)
    REACTIVE_POWER                = (244, 18)
    RMS_CURRENT                   = (280, 18)
    RMS_CURRENT_1_MIN_AVERAGE     = (316, 18)
    RMS_VOLTAGE                   = (352, 18)
    RMS_VOLTAGE_1_MIN_AVERAGE     = (388, 18)
    FREQUENCY                     = (424, 18)


class EcoAdaptModbus:
    """ Class used to listen to EcoAdapt device and expose it's data through a queue. """

    def __init__(self, address: str, port: int, unit, read_time_interval_s: int,
                 queue: asyncio.queues.Queue):
        """ Constructor of the the class who is in charge to gather data from EcoAdapt device.

        :param address: Modbus IP address.
        :param port: Modbus port.
        :param unit: Modbus unit.
        :param read_time_interval_s: time interval between each read to the modbus device.
        :param queue: asyncio queue where the data from modbus device will be stored.
        """
        self._address = address
        self._port = port
        self._unit = unit
        self._read_time_interval_s = read_time_interval_s
        self._queue = queue

    async def read_task(self):
        """ Async task that can be used to read Periodically read the data from PowerElec. """
        while True:
            registers = self._read_registers()
            await self._queue.put(registers)  # Send data to the queue
            await asyncio.sleep(self._read_time_interval_s)  # Wait before next read

    def _read_registers(self) -> tuple:
        """ Read data registers from Eco Elec 6 through modbus. """
        registers = list()
        log.info("Setting up client")
        client = ModbusClient(self._address, port=self._port)
        client.connect()

        log.info("Reading registers")
        read_registers = [
            EcoElec6Register.SOFTWARE_VERSION,
            EcoElec6Register.MODBUS_TABLE_VERSION,
            EcoElec6Register.MAC_ADDRESS,
            EcoElec6Register.RMS_VOLTAGE,
            EcoElec6Register.FREQUENCY
        ]
        for r in read_registers:
            resp = client.read_input_registers(r.value[0], r.value[1], unit=self._unit)
            log.info("%s: %s: %s" % (r, resp, resp.registers))

        log.info("Closing client")
        client.close()

        return tuple(registers)


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


class ExporterEcoAdapt():
    """ Class that can gather data from a Power Elec 6 through ModBus and
    push that data to a cloud server using websockets.
    """
    def __init__(self, cloud_url: str, modbus_address: str, modbus_port: int, modbus_unit):
        """ Exporter Eco Adapt constructor.

        :param cloud_url: the URL of the cloud server where the data will be sent.
        :param modbus_address: Modbus IP address.
        :param modbus_port: Modbus port.
        :param modbus_unit: Modbus unit.
        """
        self._queue = asyncio.Queue()
        self._cloud_client = WebSocketClient(cloud_url)
        self._modbus_client = EcoAdaptModbus(modbus_address, modbus_port, modbus_unit)


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
