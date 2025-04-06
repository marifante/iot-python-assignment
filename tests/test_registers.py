import pytest

from exporter_ecoadapt.registers import (
    decode_f32_circuit_info_data_register, decode_software_version, decode_modbus_table_version, 
    decode_mac_address
)


## Test function to decode software version ###################################
@pytest.mark.parametrize(
    ("input_registers_data", "expected_decoded_data"),
    [
        ([0x0106], "1.6"),
        ([0x0255], "2.85"),
        ([0x9999], "153.153")
    ]
)
def test_decode_software_version_good_weather(input_registers_data, expected_decoded_data):
    """ Test if the function to decode software version works correctly in a good weather scenario. """
    obtained_decoded_data = decode_software_version(data=input_registers_data)
    assert expected_decoded_data == obtained_decoded_data

@pytest.mark.parametrize(
    ("input_registers_data"),
    [
        ([0x0106, 142]),
        ([]),
    ]
)
def test_decode_software_version_bad_weather(input_registers_data):
    """ Test if the function to decode software version triggers an exception in cases in
    which the input data doesn't has the correct format. """
    with pytest.raises(ValueError):
        decode_software_version(data=input_registers_data)


## Test function to decode modbus table version ###############################
@pytest.mark.parametrize(
    ("input_registers_data", "expected_decoded_data"),
    [
        ([0x0106], 262),
        ([0x0002], 2),
        ([0x9999], 39321)
    ]
)
def test_decode_modbus_table_version_good_weather(input_registers_data, expected_decoded_data):
    """ Test if the function to decode modbus table version works correctly in a good weather scenario. """
    obtained_decoded_data = decode_modbus_table_version(data=input_registers_data)
    assert expected_decoded_data == obtained_decoded_data

@pytest.mark.parametrize(
    ("input_registers_data"),
    [
        ([0x0106, 142]),
        ([]),
    ]
)
def test_decode_modbus_table_version_bad_weather(input_registers_data):
    """ Test if the function to decode modbus table version triggers an exception in cases in
    which the input data doesn't has the correct format. """
    with pytest.raises(ValueError):
        decode_modbus_table_version(data=input_registers_data)

## Test function to decode mac address ########################################
@pytest.mark.parametrize(
    ("input_registers_data", "expected_decoded_data"),
    [
        ([30, 44285, 17639],    "001EACFD44E7"),
        ([0x1, 0x2, 0x3],       "000100020003"),
        ([0xFFFF, 0x0, 0xFFFF], "FFFF0000FFFF")
    ]
)
def test_decode_mac_address_good_weather(input_registers_data, expected_decoded_data):
    """ Test if the function to decode mac address works correctly in a good weather scenario. """
    obtained_decoded_data = decode_mac_address(data=input_registers_data)
    assert expected_decoded_data == obtained_decoded_data

@pytest.mark.parametrize(
    ("input_registers_data"),
    [
        ([0x01, 142]),
        ([],),
        ([0x24, 0xAB, 2451, 2223])
    ]
)
def test_decode_mac_address_bad_weather(input_registers_data):
    """ Test if the function to decode mac address triggers an exception in cases in
    which the input data doesn't has the correct format. """
    with pytest.raises(ValueError):
        decode_mac_address(data=input_registers_data)

## Test function to decode float32 circuit info data registers ################
@pytest.mark.parametrize(
    ("input_registers_data", "expected_decoded_data"),
    [
        (
            [49709, 17262,         20887, 15905,       45177, 15748]        + [0]   * 30,
            (238.7584991455078125, 0.1575378030538558, 0.06478971987962722) + (0, ) * 15
        ),
        (
            [34030, 17262,         13400, 15907,       22707, 15748]        + [0]   * 30,
            (238.519256591796875,  0.1593793630599975, 0.06462230533361434) + (0, ) * 15
        ),
        (
            [0]   * 36,
            (0, ) * 18
        ),
        (
            [0x94D6, 0x42FF]   * 18,
            (127.79069519042968757, ) * 18
        ),
        (
            [0x6666, 0x4248]        + [0]   * 34,
            (50.099998474121094, )  + (0, ) * 17
        ),

    ]
)
def test_decode_f32_circuit_info_data_register_good_weather(input_registers_data, expected_decoded_data):
    """ Test if the function to decode float32 data registers works correctly in a good weather scenario. """
    obtained_decoded_data = decode_f32_circuit_info_data_register(data=input_registers_data)
    assert obtained_decoded_data == pytest.approx(expected_decoded_data)

@pytest.mark.parametrize(
    ("input_registers_data"),
    [
        ([0x01, 142]),
        ([],),
        ([0x24, 0xAB, 2451, 2223])
    ]
)
def test_decode_f32_circuit_info_data_register_bad_weather(input_registers_data):
    """ Test if the function to decode float32 data registers triggers an exception in cases in
    which the input data doesn't has the correct format. """
    with pytest.raises(ValueError):
        decode_f32_circuit_info_data_register(data=input_registers_data)
