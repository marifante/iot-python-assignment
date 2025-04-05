"""
Modbus client used to read data from Power Elec 6 devices.
This client only knows about modbus.
It will read the specified data registers from the device using modbus, it will
format them (using a callback specified at object-creation) and then it will send them
through a queue.
"""
import asyncio
import logging
from typing import Callable

from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient as ModbusClient
from pymodbus.client.asynchronous import schedulers

log = logging.getLogger(__name__)


class EcoAdaptModbus:
    """ Class used to listen to EcoAdapt device and expose it's data through a queue. """

    def __init__(self, address: str, port: int, read_time_interval_s: int,
                       queue: asyncio.queues.Queue,
                       general_data_registers: tuple, circuits_data_registers: tuple,
                       format_data_funct: Callable,
                       loop,
                       connect_timeout: int = 10):
        """ Constructor of the the class who is in charge to gather data from EcoAdapt device.

        :param address: Modbus IP address.
        :param port: Modbus port.
        :param read_time_interval_s: time interval between each read to the modbus device.
        :param queue: asyncio queue where the data from modbus device will be stored.
        :param general_data_registers: the names of the general data registers of the device that will be read.
        :param circuits_data_registers: the names of the information per circuit data registers that will be read.
        :param format_data_funct: callback used to format the data registers once those are read.
        :param loop: asyncio loop where the client will be executed.
        :param connect_timeout: seconds to wait until the client connects to the device.
        """
        self._address = address
        self._port = port
        self._read_time_interval_s = read_time_interval_s
        self._queue = queue
        self._loop = loop
        self._connect_timeout = connect_timeout
        self._general_data_registers = general_data_registers
        self._circuits_data_registers = circuits_data_registers
        self._data_registers_to_export = general_data_registers + circuits_data_registers

        self._format_data_funct = format_data_funct

    async def read_registers(self) -> tuple:
        """ Read data registers from Power Elec 6 through modbus.

        This will connect to the device, read the data registers and then disconnect.
        Here we read all the exported data registers at once, without
        classifying them.

        In case an error is detected during modbus reading, the exception will be handled
        and an empty tuple will be returned.

        :return: a tuple with the information of each circuit of the Power Elec 6 device.
        """
        registers_data = list()

        log.info("Setting up client")
        _, client = ModbusClient(schedulers.ASYNC_IO, host=self._address, port=self._port,
                                 loop=self._loop)

        try:
            log.info("Connecting to modbus device on {self._address}")
            await asyncio.wait_for(client.protocol.connect(), self._connect_timeout)

            log.info(f"Reading registers: {', '.join([x.name for x in self._data_registers_to_export])}")

            for r in self._data_registers_to_export:
                resp = await client.protocol.read_input_registers(address=r.value[0], count=r.value[1], slave=1)
                registers_data.append((r, resp.registers, ))
                log.info(f"{r.name} {r.value[0], r.value[1]}: {resp}: {resp.registers}")

        except asyncio.TimeoutError:
            log.warning(f"Connection timed out after {self._connect_timeout} seconds")
            registers_data = []
        except Exception as e:
            log.error(f"Exception '{e}' occurred during modbus reading.")
            registers_data = []

        log.info("Closing client")
        client.protocol.close()

        return tuple(registers_data)

    async def task(self):
        """ Async task that can be used to read periodically read the data from PowerElec. """
        while True:
            registers = await self.read_registers()
            if registers:
                await self._queue.put(self._format_data_funct(registers))  # Send data to the queue

            await asyncio.sleep(self._read_time_interval_s)  # Wait before next read


