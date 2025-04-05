import pytest

from exporter_ecoadapt.registers import PowerElec6Register
from exporter_ecoadapt.exported_data import _format_circuit_data, create_protobuf_struct, create_binary_packet  # Adjust the import based on your module structure
import exporter_ecoadapt.generated.power_elec6_message_pb2 as protobuf


@pytest.mark.parametrize(
    "unordered_circuit_data, expected",
    [
        (
            {
                PowerElec6Register.CIRCUIT_CONFIGURATION.name: [1, 2, 3],
                PowerElec6Register.RMS_VOLTAGE.name: [220, 230, 240],
                PowerElec6Register.FREQUENCY.name: [50, 60, 50],
            },
            [
                (1, 1, 1, 220, 50),
                (1, 2, 2, 230, 60),
                (1, 3, 3, 240, 50),
            ]
        ),
        (
            {
                PowerElec6Register.CIRCUIT_CONFIGURATION.name: [x for x in range(18, 0, -1)],
                PowerElec6Register.RMS_VOLTAGE.name: [
                    0.03,  0.12,  -0.08,
                    0.00,  228.5,  231.2,
                    222.3, 240.1,  229.8,
                    235.0, 211.4,  244.7,
                    224.2, 237.6,  209.3,
                    247.8, 232.9,  218.5
                ],
                PowerElec6Register.FREQUENCY.name: [
                    0.02, -0.03,  0.05,
                    0.00,  49.1,  50.7,
                    47.3,  52.6,  45.8,
                    54.2,  46.5,  48.9,
                    51.1,  53.4,  49.7,
                    50.0,  47.8,  46.9
                ]
            },
            [
                (1, 1, 18,  0.03,  0.02),
                (1, 2, 17,  0.12, -0.03),
                (1, 3, 16, -0.08,  0.05),
                (2, 1, 15,  0.00,  0.00),
                (2, 2, 14,  228.5, 49.1),
                (2, 3, 13,  231.2, 50.7),
                (3, 1, 12,  222.3, 47.3),
                (3, 2, 11,  240.1, 52.6),
                (3, 3, 10,  229.8, 45.8),
                (4, 1, 9,   235.0, 54.2),
                (4, 2, 8,   211.4, 46.5),
                (4, 3, 7,   244.7, 48.9),
                (5, 1, 6,   224.2, 51.1),
                (5, 2, 5,   237.6, 53.4),
                (5, 3, 4,   209.3, 49.7),
                (6, 1, 3,   247.8, 50.0),
                (6, 2, 2,   232.9, 47.8),
                (6, 3, 1,   218.5, 46.9),
            ]
        )
    ]
)
def test_format_circuit_data_good_weather(unordered_circuit_data, expected):
    """ Test a good weather scenario with diverse input data. """
    result = _format_circuit_data(unordered_circuit_data)
    for idx, circuit_info in enumerate(result):
        assert expected[idx][0] == circuit_info.connector, f"connector doesn't match in iteration {idx}"
        assert expected[idx][1] == circuit_info.channel, f"channel doesn't match in iteration {idx}"
        assert expected[idx][2] == circuit_info.configuration, f"circuit configuration doesn't match in iteration {idx}"
        assert expected[idx][3] == pytest.approx(circuit_info.rms_voltage), f"rms voltage doesn't match in iteration {idx}"
        assert expected[idx][4] == pytest.approx(circuit_info.frequency), f"frequency doesn't match in iteration {idx}"


@pytest.mark.parametrize(
    "unordered_circuit_data",
    [
        {
            PowerElec6Register.CIRCUIT_CONFIGURATION.name: [1, 2, 3],
        },
        dict(),
        "astr",
        154
    ]
)
def test_format_circuit_data_bad_input_data(unordered_circuit_data):
    """ Test if an exception is raised if the input data has an incorrect format. """
    with pytest.raises(ValueError):
        _format_circuit_data(unordered_circuit_data)


@pytest.fixture
def fixed_input_registers_data_fixture():
    """ Create a fixed input data to test the functions to create protobuf.

    The first element of the tuple are the registers data.
    The second element is the expected protobuf struct that should be created.
    The third is the binary protobuf packet that should be created.
    """
    return (
        (
            (PowerElec6Register.SOFTWARE_VERSION,       [0x0109]),
            (PowerElec6Register.MODBUS_TABLE_VERSION,   [2]),
            (PowerElec6Register.MAC_ADDRESS,            [0x0011, 0x2233, 0x4455]),
            (PowerElec6Register.CIRCUIT_CONFIGURATION,  [0x4, 0x5, 0x7]),
            (PowerElec6Register.RMS_VOLTAGE,            [49709, 17262,   0, 0,  22707, 15748]   + [0, 0] * 15),
            (PowerElec6Register.FREQUENCY,              [0x6666, 0x4248, 0, 0,  0x6666, 0x4248] + [0, 0] * 15),
        ),
        protobuf.PowerElec6Message(
            software_version = "1.9",
            modbus_table_version = 2,
            mac_address = "001122334455",
            circuits_info = [
                protobuf.PowerElec6CircuitInfo(
                    connector=1,
                    channel=1,
                    configuration=4,
                    rms_voltage=238.7584991455078125,
                    frequency=50.099998474121094
                ),
                protobuf.PowerElec6CircuitInfo(
                    connector=1,
                    channel=2,
                    configuration=5,
                    rms_voltage=0.0,
                    frequency=0.0
                ),
                protobuf.PowerElec6CircuitInfo(
                    connector=1,
                    channel=3,
                    configuration=7,
                    rms_voltage=0.06462230533361435,
                    frequency=50.099998474121094
                )
            ]
        ),
        b'\n\x031.9\x10\x02\x1a\x0c001122334455"\x10\x08\x01\x10\x01\x18\x04%-\xc2nC-ffHB"\x06\x08\x01\x10\x02\x18\x05"\x10\x08\x01\x10\x03\x18\x07%\xb3X\x84=-ffHB'
        )


def test_create_protobuf_struct(fixed_input_registers_data_fixture):
    """ Test if we can create a protobuf struct using some fixed input data. """
    input_data_registers = fixed_input_registers_data_fixture[0]
    expected_protobuf_struct = fixed_input_registers_data_fixture[1]

    result = create_protobuf_struct(input_data_registers)

    assert expected_protobuf_struct.software_version == result.software_version
    assert expected_protobuf_struct.modbus_table_version == result.modbus_table_version
    assert expected_protobuf_struct.mac_address == result.mac_address
    assert len(result.circuits_info) == 3

    for idx, _ in enumerate(result.circuits_info):
        assert expected_protobuf_struct.circuits_info[idx].connector == result.circuits_info[idx].connector
        assert expected_protobuf_struct.circuits_info[idx].channel == result.circuits_info[idx].channel
        assert expected_protobuf_struct.circuits_info[idx].configuration == result.circuits_info[idx].configuration
        assert expected_protobuf_struct.circuits_info[idx].rms_voltage == result.circuits_info[idx].rms_voltage
        assert expected_protobuf_struct.circuits_info[idx].frequency == result.circuits_info[idx].frequency


def test_create_binary_packet(fixed_input_registers_data_fixture):
    """ Test if we can create a protobuf binary packet using some fixed input data. """
    input_data_registers = fixed_input_registers_data_fixture[0]
    expected_protobuf_binary = fixed_input_registers_data_fixture[2]

    result = create_binary_packet(input_data_registers)

    assert isinstance(result, bytes)
    assert expected_protobuf_binary == result
