import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, call

from exporter_ecoadapt.exporter_ecoadapt import EcoAdaptModbus, ExportedCircuitData, ExportedConnectorData
from exporter_ecoadapt.registers import EcoElec6Register


@pytest.fixture
def eco_adapt_modbus():
    # Setup before each test
    address = "192.168.1.100"
    port = 502
    read_time_interval_s = 2
    queue = asyncio.Queue()
    return EcoAdaptModbus(address, port, read_time_interval_s, queue)


@pytest.mark.parametrize(
    ("input_registers_data", "expected_output_packet"),
    [
        # First test case where all the same data (easy test to setup)
        (
            (   (EcoElec6Register.SOFTWARE_VERSION,         [0x0106]),
                (EcoElec6Register.MODBUS_TABLE_VERSION,     [0x2]),
                (EcoElec6Register.MAC_ADDRESS,              [0x00AE, 0x0001, 0x002C]),
                (EcoElec6Register.CIRCUIT_CONFIGURATION,    [0x1] * 18),
                (EcoElec6Register.RMS_VOLTAGE,              [49709, 17262] * 18),
                (EcoElec6Register.FREQUENCY,                [0x6666, 0x4248] * 18),
            ),
            {
                EcoElec6Register.SOFTWARE_VERSION.name: "1.6",
                EcoElec6Register.MODBUS_TABLE_VERSION.name: 2,
                EcoElec6Register.MAC_ADDRESS.name: "00AE0001002C",
                "CIRCUITS": (
                    ExportedConnectorData(connector=1, channel=1, data=ExportedCircuitData(1, 238.7584991455078125, 50.099998474121094)),
                    ExportedConnectorData(connector=1, channel=2, data=ExportedCircuitData(1, 238.7584991455078125, 50.099998474121094)),
                    ExportedConnectorData(connector=1, channel=3, data=ExportedCircuitData(1, 238.7584991455078125, 50.099998474121094)),
                    ExportedConnectorData(connector=2, channel=1, data=ExportedCircuitData(1, 238.7584991455078125, 50.099998474121094)),
                    ExportedConnectorData(connector=2, channel=2, data=ExportedCircuitData(1, 238.7584991455078125, 50.099998474121094)),
                    ExportedConnectorData(connector=2, channel=3, data=ExportedCircuitData(1, 238.7584991455078125, 50.099998474121094)),
                    ExportedConnectorData(connector=3, channel=1, data=ExportedCircuitData(1, 238.7584991455078125, 50.099998474121094)),
                    ExportedConnectorData(connector=3, channel=2, data=ExportedCircuitData(1, 238.7584991455078125, 50.099998474121094)),
                    ExportedConnectorData(connector=3, channel=3, data=ExportedCircuitData(1, 238.7584991455078125, 50.099998474121094)),
                    ExportedConnectorData(connector=4, channel=1, data=ExportedCircuitData(1, 238.7584991455078125, 50.099998474121094)),
                    ExportedConnectorData(connector=4, channel=2, data=ExportedCircuitData(1, 238.7584991455078125, 50.099998474121094)),
                    ExportedConnectorData(connector=4, channel=3, data=ExportedCircuitData(1, 238.7584991455078125, 50.099998474121094)),
                    ExportedConnectorData(connector=5, channel=1, data=ExportedCircuitData(1, 238.7584991455078125, 50.099998474121094)),
                    ExportedConnectorData(connector=5, channel=2, data=ExportedCircuitData(1, 238.7584991455078125, 50.099998474121094)),
                    ExportedConnectorData(connector=5, channel=3, data=ExportedCircuitData(1, 238.7584991455078125, 50.099998474121094)),
                    ExportedConnectorData(connector=6, channel=1, data=ExportedCircuitData(1, 238.7584991455078125, 50.099998474121094)),
                    ExportedConnectorData(connector=6, channel=2, data=ExportedCircuitData(1, 238.7584991455078125, 50.099998474121094)),
                    ExportedConnectorData(connector=6, channel=3, data=ExportedCircuitData(1, 238.7584991455078125, 50.099998474121094)),
                )
            },
        ),
        # Second test case where some channels have different data
        (
            (   (EcoElec6Register.SOFTWARE_VERSION,         [0x0902]),
                (EcoElec6Register.MODBUS_TABLE_VERSION,     [0x2]),
                (EcoElec6Register.MAC_ADDRESS,              [0x00AD, 0x0F01, 0x0B2C]),
                (EcoElec6Register.CIRCUIT_CONFIGURATION,    [0x1] * 18),
                (EcoElec6Register.RMS_VOLTAGE,              [49709, 17262,   0, 0,  22707, 15748]   + [0, 0] * 15),
                (EcoElec6Register.FREQUENCY,                [0x6666, 0x4248, 0, 0,  0x6666, 0x4248] + [0, 0] * 15),
            ),
            {
                EcoElec6Register.SOFTWARE_VERSION.name: "9.2",
                EcoElec6Register.MODBUS_TABLE_VERSION.name: 2,
                EcoElec6Register.MAC_ADDRESS.name: "00AD0F010B2C",
                "CIRCUITS": (
                    ExportedConnectorData(connector=1, channel=1, data=ExportedCircuitData(1, 238.7584991455078125, 50.099998474121094)),
                    ExportedConnectorData(connector=1, channel=2, data=ExportedCircuitData(1, 0.0,                  0.0)),
                    ExportedConnectorData(connector=1, channel=3, data=ExportedCircuitData(1, 0.06462230533361435,  50.099998474121094)),
                    ExportedConnectorData(connector=2, channel=1, data=ExportedCircuitData(1, 0.0,                  0.0)),
                    ExportedConnectorData(connector=2, channel=2, data=ExportedCircuitData(1, 0.0,                  0.0)),
                    ExportedConnectorData(connector=2, channel=3, data=ExportedCircuitData(1, 0.0,                  0.0)),
                    ExportedConnectorData(connector=3, channel=1, data=ExportedCircuitData(1, 0.0,                  0.0)),
                    ExportedConnectorData(connector=3, channel=2, data=ExportedCircuitData(1, 0.0,                  0.0)),
                    ExportedConnectorData(connector=3, channel=3, data=ExportedCircuitData(1, 0.0,                  0.0)),
                    ExportedConnectorData(connector=4, channel=1, data=ExportedCircuitData(1, 0.0,                  0.0)),
                    ExportedConnectorData(connector=4, channel=2, data=ExportedCircuitData(1, 0.0,                  0.0)),
                    ExportedConnectorData(connector=4, channel=3, data=ExportedCircuitData(1, 0.0,                  0.0)),
                    ExportedConnectorData(connector=5, channel=1, data=ExportedCircuitData(1, 0.0,                  0.0)),
                    ExportedConnectorData(connector=5, channel=2, data=ExportedCircuitData(1, 0.0,                  0.0)),
                    ExportedConnectorData(connector=5, channel=3, data=ExportedCircuitData(1, 0.0,                  0.0)),
                    ExportedConnectorData(connector=6, channel=1, data=ExportedCircuitData(1, 0.0,                  0.0)),
                    ExportedConnectorData(connector=6, channel=2, data=ExportedCircuitData(1, 0.0,                  0.0)),
                    ExportedConnectorData(connector=6, channel=3, data=ExportedCircuitData(1, 0.0,                  0.0)),
                )
            }
        )
    ]
)
def test_create_queue_packet_good_weather(eco_adapt_modbus, input_registers_data, expected_output_packet):
    """Test the method used to create the packet with the decoded data from the device."""
    obtained_packet = eco_adapt_modbus.create_queue_packet(input_registers_data)
    assert expected_output_packet == obtained_packet


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
