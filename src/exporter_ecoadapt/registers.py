"""
Definitions and utilities to work with the registers of Power Elec 6 device.
"""
from enum import Enum
import struct
import logging

# configure the client logging
log = logging.getLogger(__name__)


WORDS_IN_F32_CIRCUIT_INFO_REGISTERS = 36 # Quantity of words in circuit info registers


class CircuitConfiguration(Enum):
    """ Different possible configurations of each circuit. """
    DISABLED                             = 0x0000
    SINGLE_PHASE                         = 0x0001
    THREE_PHASE_WITH_NEUTRAL             = 0x0002
    BALANCED_THREE_PHASE_WITH_NEUTRAL    = 0x0003
    THREE_PHASE_WITHOUT_NEUTRAL          = 0x0004
    BALANCED_THREE_PHASE_NO_NEUTRAL      = 0x0005
    THREE_PHASE_WITH_VOLTAGE_TRANSFORMER = 0x0006


def decode_software_version(data: list) -> str:
    """ Decode a software version data register.

    :param data: a list with the fields of this data register.
    :return: a string with the software version contained in the register.
    """
    if len(data) != 1:
        raise ValueError("The length of this data register is different than 1! (not expected!)")

    raw_data = int(data[0])
    return f"{(raw_data >> 8) & 0xFF}.{raw_data & 0xFF}"


def decode_modbus_table_version(data: list) -> int:
    """ Decode modbus table version data register.

    :param data: a list with the fields of this data register.
    :return: an integer with the version contained in the register.
    """
    if len(data) != 1:
        raise ValueError("The length of this data register is different than 1! (not expected!)")

    return int(data[0])


def decode_mac_address(data: list) -> str:
    """ Decode mac address data register.

    :param data: a list with the fields of this data register.
    :return: a string with the mac address contained in the register.
    """
    if len(data) != 3:
        raise ValueError("The length of this data register is different than 3! (not expected!)")

    return f"{data[0]:04X}{data[1]:04X}{data[2]:04X}"


def decode_f32_circuit_info_data_register(data: list) -> tuple:
    """ Decode a circuit information float32 data register.

    In some circuit information input registers there is the information of
    all the circuits that the device can handle at the same time.
    Each circuit is a pair (connector, channel), and we have 3 channels per connectors.

    Each circuit's value is encoded in float32, so we need to read 2 contiguous registers
    (each int16) to build a value.
    a current/voltage value.

    :return: a tuple where each value corresponds to a given connector/channel.
    The first element is the (connector 0, channel 0) and the last is the (connector 6, channel 3).
    """
    if len(data) != WORDS_IN_F32_CIRCUIT_INFO_REGISTERS:
        raise ValueError(f"The length of this data register is different than {WORDS_IN_F32_CIRCUIT_INFO_REGISTERS}! (not expected!)")

    decoded_data = list()
    for idx in range(0, WORDS_IN_F32_CIRCUIT_INFO_REGISTERS, 2):
        combined_int = (data[idx] & 0xFFFF) | ((data[idx+1] << 16) & 0xFFFF0000)
        decoded_data.append( struct.unpack("!f", combined_int.to_bytes(length=4))[0] )

    return tuple(decoded_data)


class EcoElec6Register(Enum):
    """ Enum with information about the input registers of Eco Elec 6 device.
    Each member has a tuple which information:
    * First member: The start of the register.
    * Second member: The quantity of words (uint16) in the register.
    * Third member: A function that can be used to decode the content of a data register of that type.
    """
    # General information
    SOFTWARE_VERSION              = (0,   1, decode_software_version)
    MODBUS_TABLE_VERSION          = (1,   1, decode_modbus_table_version)
    MAC_ADDRESS                   = (2,   3, decode_mac_address)

    # Information per circuit
    CIRCUIT_CONFIGURATION         = (8,   WORDS_IN_F32_CIRCUIT_INFO_REGISTERS, None) # We'll use the raw data that comes from this register
    ACTIVE_ENERGY_IMPORT_INDEX    = (28,  WORDS_IN_F32_CIRCUIT_INFO_REGISTERS, None)
    REACTIVE_ENERGY_IMPORT_INDEX  = (64,  WORDS_IN_F32_CIRCUIT_INFO_REGISTERS, None)
    ACTIVE_ENERGY_EXPORT_INDEX    = (100, WORDS_IN_F32_CIRCUIT_INFO_REGISTERS, None)
    REACTIVE_ENERGY_EXPORT_INDEX  = (136, WORDS_IN_F32_CIRCUIT_INFO_REGISTERS, None)
    ACTIVE_POWER                  = (172, WORDS_IN_F32_CIRCUIT_INFO_REGISTERS, None)
    REACTIVE_POWER                = (244, WORDS_IN_F32_CIRCUIT_INFO_REGISTERS, None)
    RMS_CURRENT                   = (280, WORDS_IN_F32_CIRCUIT_INFO_REGISTERS, decode_f32_circuit_info_data_register) # We don't care about circuit information here (it is circuit or phase)
    RMS_CURRENT_1_MIN_AVERAGE     = (316, WORDS_IN_F32_CIRCUIT_INFO_REGISTERS, decode_f32_circuit_info_data_register) # We don't care about circuit information here (it is circuit or phase)
    RMS_VOLTAGE                   = (352, WORDS_IN_F32_CIRCUIT_INFO_REGISTERS, decode_f32_circuit_info_data_register) # We don't care about circuit information here (it is circuit or phase)
    RMS_VOLTAGE_1_MIN_AVERAGE     = (388, WORDS_IN_F32_CIRCUIT_INFO_REGISTERS, decode_f32_circuit_info_data_register) # We don't care about circuit information here (it is circuit or phase)
    FREQUENCY                     = (424, WORDS_IN_F32_CIRCUIT_INFO_REGISTERS, decode_f32_circuit_info_data_register) # In 3-phase all channels should report the same freq, otherwise each channel will report a different freq (don't make a distintion here)
