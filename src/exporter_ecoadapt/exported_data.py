"""
Functions used to format the data that comes from PowerElec6 device to a format
that can be sent to the cloud server.
The data of the device that will be push to the cloud server is already fixed
by protobuf .proto file. So we don't need to some dynamic fancy logic here.
The idea is to maintain in this file all the knowledge about what information
is sent to the server.
"""
import logging
import exporter_ecoadapt.generated.power_elec6_message_pb2 as protobuf
from exporter_ecoadapt.registers import PowerElec6Register

log = logging.getLogger(__name__)


# Generic data of the device
DEVICE_GENERAL_DATA_REGISTERS = (
                                    PowerElec6Register.SOFTWARE_VERSION,
                                    PowerElec6Register.MODBUS_TABLE_VERSION,
                                    PowerElec6Register.MAC_ADDRESS
                                )

# Data that the devices has per circuit
DEVICE_CIRCUIT_DATA_REGISTERS = (
                                    PowerElec6Register.CIRCUIT_CONFIGURATION,
                                    PowerElec6Register.RMS_VOLTAGE,
                                    PowerElec6Register.FREQUENCY
                                )


def _format_circuit_data(unordered_circuit_data: dict) -> list:
    """ Take a dictionary with raw data from the device and separate it
    by connector and channel.

    :param unordered_circuit_data: a dictionary with the following format, where
    each key, value pair is a circuit info parameter (key) and an array
    with the data of every conector/channel pair.
    :return: a list where each element is a protobuf PowerElec6CircuitInfo struct that holds
    the connector, channel, configuration, rms_voltage and frequency data of a circuit.
    """
    if not isinstance(unordered_circuit_data, dict):
        raise ValueError(f"Input data is not a dictionary ({type(unordered_circuit_data)})")

    if not all(key.name in unordered_circuit_data for key in DEVICE_CIRCUIT_DATA_REGISTERS):
        raise ValueError(f"A data register is missing from input dictionary: {unordered_circuit_data}")

    formatted_data = list()

    for idx in range(0, len(unordered_circuit_data[PowerElec6Register.CIRCUIT_CONFIGURATION.name])):
        connector = idx // 3 + 1
        channel = idx % 3 + 1
        log.debug(f"Adding data for connector {connector} channel {channel}")

        formatted_data.append(
            protobuf.PowerElec6CircuitInfo(
                connector = connector,
                channel = channel,
                configuration = unordered_circuit_data[PowerElec6Register.CIRCUIT_CONFIGURATION.name][idx],
                rms_voltage = unordered_circuit_data[PowerElec6Register.RMS_VOLTAGE.name][idx],
                frequency = unordered_circuit_data[PowerElec6Register.FREQUENCY.name][idx]
            )
        )

    return formatted_data

def create_protobuf_struct(registers_data: tuple) -> protobuf.PowerElec6Message:
    """ Create a protobuf struct with the data from PowerElec 6 device.

    In order to do this, we decode the raw data that was read from the device.
    So, we traverse through the data registers.
    Luckily, the generic data can be decoded and directly assigned to the packet.
    Sadly, the data per circuit needs more care. So we decode it and later on
    we split the data by connector and channel.

    :param registers_data: a tuple with the data registers in a determined order.
    Each element of this tuple is another tuple, where the first element is
    the metadata of the data register and the second one is the content of those
    data registers.
    For instance:

    [0]   = (SOFTWARE_VERSION, data[])
    [1]   = (MODBUS_TABLE_VERSION. data[])
    [2]   = (MAC_ADDRESS, data[])
    [3]   = (CIRCUIT_CONFIGURATION, data[])
    [4]   = (RMS_VOLTAGE, data[])
    [5]   = (FREQUENCY, data[])

    :return: the protobuf struct with the information of the device.
    """
    message = protobuf.PowerElec6Message()

    unordered_circuit_data = { data_reg.name: [] for data_reg in DEVICE_CIRCUIT_DATA_REGISTERS }

    # Generic info is easy, just add it to the packet
    message.software_version = registers_data[0][0].decode(registers_data[0][1])
    message.modbus_table_version = registers_data[1][0].decode(registers_data[1][1])
    message.mac_address = registers_data[2][0].decode(registers_data[2][1])

    # Circuit info has encoded the values of each connector/channel, we need to separate it
    for reg in registers_data:
        unordered_circuit_data[ reg[0].name ] = reg[0].decode(reg[1])

    log.info(f"unordered_circuit_data = {unordered_circuit_data}")
    message.circuits_info.extend( _format_circuit_data(unordered_circuit_data) )

    log.info(f"len(message.circuits_info) = {message.circuits_info}")
    return message

def create_binary_packet(registers_data: tuple) -> bytes:
    """ Create a protobuf binary packet with the data stored in device's data registers.

    :param registers_data: a tuple with the data registers in a determined order.
    Each element of this tuple is another tuple, where the first element is
    the metadata of the data register and the second one is the content of those
    data registers.
    For instance:

    [0]   = (SOFTWARE_VERSION, data[])
    [1]   = (MODBUS_TABLE_VERSION. data[])
    [2]   = (MAC_ADDRESS, data[])
    [3]   = (CIRCUIT_CONFIGURATION, data[])
    [4]   = (RMS_VOLTAGE, data[])
    [5]   = (FREQUENCY, data[])

    :return: the protobuf binary packet.
    """
    return create_protobuf_struct(registers_data).SerializeToString()
