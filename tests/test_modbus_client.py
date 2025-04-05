import pytest
import asyncio
from asynctest.mock import MagicMock, CoroutineMock
from asynctest.mock import Mock
from asynctest import patch

from exporter_ecoadapt.modbus_client import EcoAdaptModbus
import exporter_ecoadapt.exported_data as exported_data


@pytest.fixture
def queue():
    return asyncio.Queue()


@pytest.fixture
def format_data_funct():
    return MagicMock(return_value="formatted_data")


@pytest.fixture
def eco_adapt_modbus(queue, format_data_funct):
    address = '127.0.0.1'
    port = 502
    read_time_interval_s = 1
    general_data_registers = exported_data.DEVICE_GENERAL_DATA_REGISTERS
    circuits_data_registers = exported_data.DEVICE_CIRCUIT_DATA_REGISTERS
    return EcoAdaptModbus(address, port, read_time_interval_s, queue,
                          general_data_registers, circuits_data_registers, format_data_funct)


@pytest.fixture
def mocked_modbus_client():
    """ Mock modbus client library with async mocks. """
    mock_client = Mock()
    with patch("exporter_ecoadapt.modbus_client.ModbusClient", return_value=mock_client):
        mock_client.connect = CoroutineMock(return_value=True)
        mock_client.close = MagicMock(return_value=True)
        yield mock_client


@pytest.fixture
def mocked_registers_data():
    """ Mocked registers data that can be used throughout the tests.

    The first element of the returned tuple are the mocks, they contain a
    "register" attribute, mocking the pymodbus returned data.
    The second element is a list with the data in order.
    """
    software_version =      [0x106]
    modbus_table_version =  [0x2]
    mac_address =           [0x0012, 0xAABB, 0xCCDD]
    circuit_configuration = [5, 4, 6]                               + [0] * 15
    rms_voltage =           [49709, 17262,   0, 0,  22707, 15748]   + [0, 0] * 15
    frequency =             [0x6666, 0x4248, 0, 0,  0x6666, 0x4248] + [0, 0] * 15

    return (
            [
                MagicMock(registers=software_version),
                MagicMock(registers=modbus_table_version),
                MagicMock(registers=mac_address),
                MagicMock(registers=circuit_configuration),
                MagicMock(registers=rms_voltage),
                MagicMock(registers=frequency),
            ],
            [
                software_version,
                modbus_table_version,
                mac_address,
                circuit_configuration,
                rms_voltage,
                frequency
            ]
        )


@pytest.mark.asyncio
async def test_read_registers_good_weather(eco_adapt_modbus, mocked_modbus_client, mocked_registers_data):
    """ Test a case in which we can read data from the device using modbus library. """
    # Arrange: Mock the response of the modbus client
    mocked_input_registers = mocked_registers_data[0]
    expected_registers_data = mocked_registers_data[1]
    mocked_modbus_client.read_input_registers = CoroutineMock(side_effect=mocked_input_registers)

    # Act: read the data using modbus lib but mocked
    registers_data = await eco_adapt_modbus.read_registers()

    # Assert:
    assert len(registers_data) == 6
    for idx, expected_data in enumerate(expected_registers_data):
        assert expected_data == registers_data[idx][1]


@pytest.mark.asyncio
async def test_read_registers_bad_weather(eco_adapt_modbus, mocked_modbus_client):
    """ Mock a failure in modbus client (an exception should be arised, pymodbus is responsible by it). """
    # Arrange: Mock pymodbus method to read input registers, forcing an exception
    mocked_modbus_client.read_input_registers = Mock(side_effect=Exception("Modbus read failed"))

    # Act: read the data using modbus lib but mocked
    registers_data = await eco_adapt_modbus.read_registers()

    # Assert: Check if an empty tuple was returned
    assert len(registers_data) == 0


@pytest.mark.asyncio
async def test_periodic_task_good_weather(eco_adapt_modbus, mocked_modbus_client, mocked_registers_data, queue):
    """ Test the async task used to read data from the device periodically. """
    # Arrange: Mock the response from modbus client and then create the task
    mocked_input_registers = mocked_registers_data[0]
    mocked_modbus_client.read_input_registers = CoroutineMock(side_effect=mocked_input_registers)

    task = asyncio.create_task(eco_adapt_modbus.task())

    # Act: Run the task for a short period and then cancel it
    await asyncio.sleep(eco_adapt_modbus._read_time_interval_s * 0.5)
    task.cancel()

    # Assert: Check if data was put into the queue
    assert not queue.empty()
    data = await queue.get()

    assert data == "formatted_data" # the format data function is mocked to return this string


@pytest.mark.asyncio
async def test_task_bad_weather(eco_adapt_modbus, mocked_modbus_client, queue):
    """ Mock a failure in modbus client when the periodic task is executed
    (an exception should be arised, pymodbus is responsible by it).
    """
    # Arrange: Mock a failure in modbus client read registers method
    mocked_modbus_client.read_input_registers = Mock(side_effect=Exception("Modbus read failed (error type X)"))

    task = asyncio.create_task(eco_adapt_modbus.task())

    # Act: Run the task for a short period and then cancel it
    await asyncio.sleep(eco_adapt_modbus._read_time_interval_s * 2)

    # Assert: Check if the queue is empty since no data should be put due to exception
    assert queue.empty()
    assert not task.cancelled()

    task.cancel()
