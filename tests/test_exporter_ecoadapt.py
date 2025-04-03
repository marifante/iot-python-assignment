import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, call

from exporter_ecoadapt.exporter_ecoadapt import EcoAdaptModbus
from exporter_ecoadapt.registers import EcoElec6Register


@pytest.fixture
def eco_adapt_modbus():
    # Setup before each test
    address = "192.168.1.100"
    port = 502
    read_time_interval_s = 2
    queue = asyncio.Queue()
    return EcoAdaptModbus(address, port, read_time_interval_s, queue)


@pytest.mark.asyncio
async def test_read_registers(eco_adapt_modbus, mocker):
    """Test read_registers by mocking Modbus client responses."""
    expected_read_input_registers_calls = [
        call(address=r.value[0], count=r.value[1], slave=1) for r in [
            EcoElec6Register.SOFTWARE_VERSION,
            EcoElec6Register.MODBUS_TABLE_VERSION,
            EcoElec6Register.MAC_ADDRESS,
            EcoElec6Register.CIRCUIT_CONFIGURATION,
            EcoElec6Register.RMS_VOLTAGE,
            EcoElec6Register.FREQUENCY
        ]
    ]

    # Arrange: Mock Modbus client and simulate register responses
    mock_client = AsyncMock()
    mocker.patch("exporter_ecoadapt.exporter_ecoadapt.ModbusClient", return_value=mock_client)
    mock_client.connect = AsyncMock(return_value=True)
    mock_client.close = MagicMock(return_value=True)

    async def mock_read_input_registers(address, count, slave):
        _ = address
        _ = slave
        return MagicMock(registers=[42] * count)  # Simulate register response

    mock_client.read_input_registers = AsyncMock(side_effect=mock_read_input_registers)

    # Act: Call the method under test
    result = await eco_adapt_modbus.read_registers()

    # Assert: Check expected calls and results
    mock_client.connect.assert_called_once()
    mock_client.close.assert_called_once()
    mock_client.read_input_registers.assert_has_calls(expected_read_input_registers_calls, any_order=True)
    assert isinstance(result, tuple)
