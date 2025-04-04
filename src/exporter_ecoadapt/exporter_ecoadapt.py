#!/usr/bin/env python3
"""
A minimal EcoAdapt modbus reader
"""

import logging
import asyncio
from collections import namedtuple
import websockets
from pymodbus.client import AsyncModbusTcpClient as ModbusClient

from exporter_ecoadapt.registers import EcoElec6Register

# configure the client logging
log = logging.getLogger(__name__)

# Generic data of the device
DEVICE_GENERAL_DATA_REGISTERS = (
                                    EcoElec6Register.SOFTWARE_VERSION,
                                    EcoElec6Register.MODBUS_TABLE_VERSION,
                                    EcoElec6Register.MAC_ADDRESS
                                )

# Data that the devices has per circuit
DEVICE_CIRCUIT_DATA_REGISTERS = (
                                    EcoElec6Register.CIRCUIT_CONFIGURATION,
                                    EcoElec6Register.RMS_VOLTAGE,
                                    EcoElec6Register.FREQUENCY
                                )

ExportedCircuitData = namedtuple("ExportedCircuitData", [x.name for x in DEVICE_CIRCUIT_DATA_REGISTERS])
ExportedConnectorData = namedtuple("ExportedConnectorData", ["connector", "channel", "data"])

class EcoAdaptModbus:
    """ Class used to listen to EcoAdapt device and expose it's data through a queue. """

    def __init__(self, address: str, port: int, read_time_interval_s: int,
                       queue: asyncio.queues.Queue):
        """ Constructor of the the class who is in charge to gather data from EcoAdapt device.

        :param address: Modbus IP address.
        :param port: Modbus port.
        :param read_time_interval_s: time interval between each read to the modbus device.
        :param queue: asyncio queue where the data from modbus device will be stored.
        """
        self._address = address
        self._port = port
        self._read_time_interval_s = read_time_interval_s
        self._queue = queue

        self._data_registers_to_export = DEVICE_GENERAL_DATA_REGISTERS + DEVICE_CIRCUIT_DATA_REGISTERS

    async def read_task(self):
        """ Async task that can be used to read Periodically read the data from PowerElec. """
        while True:
            registers = await self.read_registers()
            await self._queue.put(registers)  # Send data to the queue
            await asyncio.sleep(self._read_time_interval_s)  # Wait before next read

    def _format_circuit_data(self, unordered_circuit_data: dict) -> tuple:
        """ Take a dictionary with raw data from the device and separate it
        by connector and channel.

        :param unordered_circuit_data: a dictionary with the following format, where
        each key, value pair is a circuit info parameter (key) and an array
        with the data of every conector/channel pair.
        """
        formatted_data = list()

        for idx in range(0, len(unordered_circuit_data[EcoElec6Register.CIRCUIT_CONFIGURATION.name])):
            connector = idx // 3 + 1
            channel = idx % 3 + 1
            log.info(f"Adding data for connector {connector} channel {channel}")

            channel_data = {
                EcoElec6Register.CIRCUIT_CONFIGURATION.name: unordered_circuit_data[EcoElec6Register.CIRCUIT_CONFIGURATION.name][idx],
                EcoElec6Register.RMS_VOLTAGE.name: unordered_circuit_data[EcoElec6Register.RMS_VOLTAGE.name][idx],
                EcoElec6Register.FREQUENCY.name: unordered_circuit_data[EcoElec6Register.FREQUENCY.name][idx],
            }

            formatted_data.append(
                ExportedConnectorData(connector=connector, channel=channel,
                                      data=ExportedCircuitData(**channel_data))
            )

        return tuple(formatted_data)

    def create_queue_packet(self, registers_data: tuple) -> dict:
        """ Create a packet that will be taken later on by the task that sends the
        data to the cloud server.

        In order to do this, we decode the raw data that was read from the device.
        So, we traverse through the data registers.
        Luckily, the generic data can be decoded and directly assigned to the packet.
        Sadly, the data per circuit needs more care. So we decode it and later on
        we split the data by connector and channel.

        :param registers_data: a tuple with the data registers to export in the order determined
        by self._data_registers_to_expor. For instance:

        [0]   = SOFTWARE_VERSION
        [1]   = MODBUS_TABLE_VERSION
        [2]   = MAC_ADDRESS
        [3]   = CIRCUIT_CONFIGURATION
        [4]   = RMS_VOLTAGE
        [5]   = FREQUENCY

        :return: the created queue packet in a dictionary.
        """
        # TODO: add timestamp
        packet = { reg.name: [] for reg in DEVICE_GENERAL_DATA_REGISTERS }
        unordered_circuit_data = { reg.name: [] for reg in DEVICE_CIRCUIT_DATA_REGISTERS }

        log.info(f"Registers_data = {registers_data}")

        for reg in registers_data:
            reg_metadata = reg[0]
            reg_data = reg[1]
            log.info(f"Inserting register data {reg} in the packet! (metadata = {reg_metadata}, data = {reg_data})")

            if reg_metadata in DEVICE_GENERAL_DATA_REGISTERS:
                packet[ reg_metadata.name ] = reg_metadata.value[2](reg_data)

            elif reg_metadata in DEVICE_CIRCUIT_DATA_REGISTERS:
                unordered_circuit_data[ reg_metadata.name ] = reg_metadata.value[2](reg_data)
                log.info(f"reg_metadata = {reg_metadata}, decoded_data = {unordered_circuit_data[ reg_metadata.name ]}")

            else:
                raise ValueError(f"Register {reg_metadata} of type {type(reg_metadata)} is not valid")

        packet["CIRCUITS"] = self._format_circuit_data(unordered_circuit_data)

        return packet

    async def read_registers(self) -> tuple:
        """ Read data registers from Eco Elec 6 through modbus.

        Here we read all the exported data registers at once, without
        classifying them.

        :return: a tuple with the information of each circuit of the Power Elec 6 device.
        """
        registers_data = list()
        log.info("Setting up client")
        client = ModbusClient(self._address, port=self._port)
        await client.connect()

        log.info(f"Reading registers: {', '.join([x.name for x in self._data_registers_to_export])}")

        for r in self._data_registers_to_export:
            resp = await client.read_input_registers(address=r.value[0], count=r.value[1], slave=1)
            registers_data.append((r, resp.registers, ))
            log.info(f"{r.name} ({r.value[0], r.value[1]}): {resp}: {resp.registers}")

        log.info("Closing client")
        client.close()

        return tuple(registers_data)


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


class ExporterEcoAdapt:
    """ Class that can gather data from a Power Elec 6 through ModBus and
    push that data to a cloud server using websockets.
    """
    def __init__(self, cloud_url: str, modbus_address: str, modbus_port: int,
                 read_time_interval_s: int):
        """ Exporter Eco Adapt constructor.

        :param cloud_url: the URL of the cloud server where the data will be sent.
        :param modbus_address: Modbus IP address.
        :param modbus_port: Modbus port.
        :param read_time_interval_s: time interval between each read to the modbus device.
        """
        self._queue = asyncio.Queue()
        self._cloud_client = WebSocketClient(cloud_url)
        self._modbus_client = EcoAdaptModbus(modbus_address, modbus_port,
                                             read_time_interval_s, self._queue)

    async def _run(self):
        """ Run exporter Eco Adapt app. """
        modbus_task = asyncio.create_task(self._modbus_client.read_task())
        #websocket_task = asyncio.create_task(websocket_client())

        # Keep running
        await asyncio.gather(modbus_task) #, websocket_task)

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
