"""
Main class that will put to run a modbus client and a cloud client.
The modbus client will gather the data from the device and the cloud client
will send it to the cloud server. That data is communicated through a queue.
Everything runs in a single thread using asyncio.
"""
import logging
import asyncio

from exporter_ecoadapt.modbus_client import EcoAdaptModbus
from exporter_ecoadapt.cloud_client import WebSocketClient
import exporter_ecoadapt.exported_data as exported_data


log = logging.getLogger(__name__)


class ExporterEcoAdapt:
    """ Class that can gather data from a Power Elec 6 through ModBus and
    push that data to a cloud server using websockets.
    """
    def __init__(self, cloud_url: str, modbus_address: str, modbus_port: int,
                 read_time_interval_s: int, loop: asyncio.AbstractEventLoop):
        """ Exporter Eco Adapt constructor.

        :param cloud_url: the URL of the cloud server where the data will be sent.
        :param modbus_address: Modbus IP address.
        :param modbus_port: Modbus port.
        :param read_time_interval_s: time interval between each read to the modbus device.
        :param loop: The event loop to be used.
        """
        self._loop = loop
        self._queue = asyncio.Queue(loop=self._loop)

        self._cloud_client = WebSocketClient(cloud_url, self._queue)
        self._modbus_client = EcoAdaptModbus(modbus_address, modbus_port,
                                             read_time_interval_s, self._queue,
                                             exported_data.DEVICE_GENERAL_DATA_REGISTERS,
                                             exported_data.DEVICE_CIRCUIT_DATA_REGISTERS,
                                             exported_data.create_binary_packet,
                                             self._loop)

    async def run(self):
        """ Run exporter Eco Adapt app. """
        modbus_task = asyncio.create_task(self._modbus_client.task())
        websocket_task = asyncio.create_task(self._cloud_client.task())

        # Keep running
        await asyncio.gather(modbus_task, websocket_task)

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
