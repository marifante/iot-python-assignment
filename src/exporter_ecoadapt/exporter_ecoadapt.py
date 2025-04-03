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


#EcoElec6CircuitInfo = namedtuple("EcoElec6CircuitInfo", ["connector", "channel", "circuit_info"])
#
#
#def decode_circuit_info_data_registers(data_registers: Tuple[Tuple[EcoElec6Register, List], ...]) -> Tuple[EcoElec6CircuitInfo, ...]:
#    """ Decode circuits information data registers data and
#    create a tuple with the circuit information of every connector's channel.
#
#    :param data_register: registers with the data of each circuit.
#    :return: a tuple that consists of EcoElec6CircuitInfo elements, whose content are the
#    parsed data from the device.
#    """
#    decoded_data = list()
#
#    tmp_dictionaries = [
#        {"connector": connector, "channel": channel, "circuit_info": None}
#        for connector in range(1, 7)  # 6 connectors (1 to 6)
#        for channel in range(1, 4)    # 3 channels per connector (1 to 3)
#    ]
#
#    # decode generic info
#    for dr in data_registers:
#        register_metadata = dr[0]
#        registers_data = dr[1]
#        decode_funct = register_metadata.value[2]
#
#        if decode_funct:
#            # decode data register
#            _decoded_data_register = decode_funct(data=registers_data)
#            print(f"dr = {register_metadata}, raw_data = {registers_data}, value = {_decoded_data_register}")
#
#            # assign the value to each channel/connector accordingly
#            for idx, tmp_dic in enumerate(tmp_dictionaries):
#                tmp_dict['circuit_info'] = 
#
#        else:
#            raise NotImplemented(f"Decoding function for circuit information register {register_metadata} is not implemented yet")
#
#
#
#    return tuple(decoded_data)
#
#
#def decode_registers_data(general_info: Tuple[Tuple[EcoElec6Register, List], ...],
#                          circuit_config: Tuple[EcoElec6Register, List],
#                          circuit_info: Tuple[Tuple[EcoElec6Register, List], ...],
#                          ) -> Tuple[EcoElec6CircuitInfo, ...]:
#    """ Decode a registers data and create a tuple with the circuit information of every connector.
#
#    :param general_info: registers with the general info of the device (software version, modbus table version, mac address).
#    :param circuit_config: registers with the configuration of each circuit.
#    :param circuit_info: registers with the data of each circuit.
#    :return: a tuple that consists of EcoElec6CircuitInfo elements, whose content are the
#    parsed data from the device.
#    """
#    decoded_data = list()
#
#    # decode generic info
#    for gir in general_info:
#        registers_data = gir[1]
#        register_metadata = gir[0]
#        decode_funct = register_metadata.value[2]
#        if decode_funct:
#            _decoded_data = decode_funct(data=registers_data)
#            print(f"gir = {register_metadata}, raw_data = {registers_data}, value = {_decoded_data}")
#        else:
#            raise NotImplemented("Decoding function for register {register_metadata} is not implemented yet")
#
#    # decode circuit config info
#
#    # decode the info of each circuit
##    for r in registers_data:
##        print(f"{r}")
##        for i in range(0, r.value[2], r.value[1]):
##            print(f"i = {i}")
#
#    return tuple(decoded_data)

# Generic data of the device
DEVICE_GENERAL_DATA_REGISTERS = [
                                    EcoElec6Register.SOFTWARE_VERSION.name,
                                    EcoElec6Register.MODBUS_TABLE_VERSION.name,
                                    EcoElec6Register.MAC_ADDRESS.name
                                ]

# Data that the devices has per circuit
DEVICE_CIRCUIT_DATA_REGISTERS = [
                                    EcoElec6Register.CIRCUIT_CONFIGURATION.name,
                                    EcoElec6Register.RMS_VOLTAGE.name,
                                    EcoElec6Register.FREQUENCY.name
                                ]

CircuitInfoPacket = namedtuple("CircuitInfoPacket", ["connector", "channel"] + DEVICE_CIRCUIT_DATA_REGISTERS )

ExportEcoAdaptPacket = namedtuple("ExporterEcoAdaptPacket", DEVICE_GENERAL_DATA_REGISTERS + ["circuits_info"])



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

    def create_queue_packet(self, registers_data: tuple) -> tuple:
        """ Create a packet that will be taken later on by the task that sends the
        data to the cloud server.

        The layout of the packet is as follows:

        [0]  = SOFTWARE_VERSION (string)
        [1]  = MODBUS_TABLE_VERSION (integer)
        [2]  = MAC_ADDRESS (string)
        [3]  = (
                (CONFIG (integer), RMS_VOLTAGE (float), FREQUENCY (float)),   # CONNECTOR 1 / CHANNEL 1
                (CONFIG (integer), RMS_VOLTAGE (float), FREQUENCY (float)),   # CONNECTOR 1 / CHANNEL 2
                (CONFIG (integer), RMS_VOLTAGE (float), FREQUENCY (float)),   # CONNECTOR 1 / CHANNEL 3
                (CONFIG (integer), RMS_VOLTAGE (float), FREQUENCY (float)),   # CONNECTOR 2 / CHANNEL 1
                (CONFIG (integer), RMS_VOLTAGE (float), FREQUENCY (float)),   # CONNECTOR 2 / CHANNEL 2
                (CONFIG (integer), RMS_VOLTAGE (float), FREQUENCY (float)),   # CONNECTOR 2 / CHANNEL 3
                (CONFIG (integer), RMS_VOLTAGE (float), FREQUENCY (float)),   # CONNECTOR 3 / CHANNEL 1
                (CONFIG (integer), RMS_VOLTAGE (float), FREQUENCY (float)),   # CONNECTOR 3 / CHANNEL 2
                (CONFIG (integer), RMS_VOLTAGE (float), FREQUENCY (float)),   # CONNECTOR 3 / CHANNEL 3
                (CONFIG (integer), RMS_VOLTAGE (float), FREQUENCY (float)),   # CONNECTOR 4 / CHANNEL 1
                (CONFIG (integer), RMS_VOLTAGE (float), FREQUENCY (float)),   # CONNECTOR 4 / CHANNEL 2
                (CONFIG (integer), RMS_VOLTAGE (float), FREQUENCY (float)),   # CONNECTOR 4 / CHANNEL 3
                (CONFIG (integer), RMS_VOLTAGE (float), FREQUENCY (float)),   # CONNECTOR 5 / CHANNEL 1
                (CONFIG (integer), RMS_VOLTAGE (float), FREQUENCY (float)),   # CONNECTOR 5 / CHANNEL 2
                (CONFIG (integer), RMS_VOLTAGE (float), FREQUENCY (float)),   # CONNECTOR 5 / CHANNEL 3
                (CONFIG (integer), RMS_VOLTAGE (float), FREQUENCY (float)),   # CONNECTOR 6 / CHANNEL 1
                (CONFIG (integer), RMS_VOLTAGE (float), FREQUENCY (float)),   # CONNECTOR 6 / CHANNEL 2
                (CONFIG (integer), RMS_VOLTAGE (float), FREQUENCY (float))    # CONNECTOR 6 / CHANNEL 3
            )
        """
        packet = {
            EcoElec6Register.SOFTWARE_VERSION.name: None,
            EcoElec6Register.MODBUS_TABLE_VERSION.name: None,
            EcoElec6Register.MAC_ADDRESS.name: None,
            "circuit_info": None
        }

        #    tmp_dictionaries = [
        #        {"connector": connector, "channel": channel, "circuit_info": None}
        #        for connector in range(1, 7)  # 6 connectors (1 to 6)
        #        for channel in range(1, 4)    # 3 channels per connector (1 to 3)
        #    ]


        for reg in registers_data:
            reg_metadata = reg[0]
            reg_data = reg[1]

            if reg_metadata in DEVICE_GENERAL_DATA_REGISTERS:
                packet[ reg_metadata.name ] = reg_metadata[2](reg_data)

            elif reg_metadata in self._device_circuit_info_registers:




    async def read_registers(self) -> tuple:
        """ Read data registers from Eco Elec 6 through modbus.

        :return: a tuple with the information of each circuit of the Power Elec 6 device.
        """
        registers_data = list()
        log.info("Setting up client")
        client = ModbusClient(self._address, port=self._port)
        await client.connect()

        log.info(f"Reading registers: {', '.join([x.name for x in self._data_registers_to_export])}")

        for r in self._data_registers_to_export:
            resp = await client.read_input_registers(address=r.value[0], count=r.value[1], slave=1)
            log.info(f"{r.name} ({r.value[0], r.value[1]}): {resp}: {resp.registers}")
            registers_data.append((r, resp.registers, ))

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
