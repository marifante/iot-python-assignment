"""
Script to simulate a fake Power Elec 6 modbus server.
It will hold hardcoded data.
"""
import argparse
import logging
import threading

from pymodbus.server.sync import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext


FORMAT = (
    "%(asctime)-15s %(threadName)-15s "
    "%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
)

logging.basicConfig(format=FORMAT, level=logging.INFO)

log = logging.getLogger(__name__)


ROTATED_DATA = [
    {
        # General information
        1: [ 0x0106 ], # Software Version
        2: [ 0x0002 ], # Modbus table Version
        3: [ 0x000A, 0x000B, 0x000C ], # MAC address

        # Information per circuit (6 circuits, 3 channels/circuit = 18 channels)
        9:   [ 0x0002 ] * 18,                       # Circuit configuration (from 8 to 25, 16-bit word per channel)
        10:  [ 0x0, 0x0 ] * 18,                     # [kWh] Active energy import index (from 28 to 63, float32 per channel)
        65:  [ 0x0, 0x0 ] * 18,                     # [kVArh] Reactive energy import index (from 64 to 99, float32 per channel)
        101: [ 0x0, 0x0 ] * 18,                     # [kWh] Active energy export index (from 100 to 135, float32 per channel)
        137: [ 0x0, 0x0 ] * 18,                     # [kVArh] Reactive energy export index (from 136 to 171, float32 per channel)
        173: [ 0x0, 0x0 ] * 18,                     # [W] Active power (from 172 to 207, float32 per channel)
        209: [ 0x0, 0x0 ] * 18,                     # [Var] Reactive power (from 208 to 243, float32 per channel)
        245: [ 0x0, 0x0 ] * 18,                     # Power factor (from 244 to 279, float32 per channel)
        281: [ 0x0, 0x0 ] * 18,                     # [A] RMS current (from 280 to 315, float32 per channel)
        317: [ 0x0, 0x0 ] * 18,                     # [A] RMS current 1 min average (from 316 to 351, float32 per channel)
        353: [ 34030, 17262 ] * 3 + [0, 0] * 15,    # [V] RMS voltage (from 352 to 387, float32 per channel)
        389: [ 0x0, 0x0 ] * 18,                     # [V] RMS voltage 1 min average (from 388 to 423, float32 per channel)
        425: [ 0x6666, 0x4248 ] * 3 + [0, 0] * 15,  # [Hz] Frequency (from 424 to 459, float32 per channel)
    },
    {
        1: [ 0x0106 ],
        2: [ 0x0002 ],
        3: [ 0x000A, 0x000B, 0x000C ],

        9:   [ 0x0002 ] * 6 + [ 0 ] * 5 + [ 0x0001 ] * 3 + [ 0 ] * 4,
        10:  [ 0x0, 0x0 ] * 18,
        65:  [ 0x0, 0x0 ] * 18,
        101: [ 0x0, 0x0 ] * 18,
        137: [ 0x0, 0x0 ] * 18,
        173: [ 0x0, 0x0 ] * 18,
        209: [ 0x0, 0x0 ] * 18,
        245: [ 0x0, 0x0 ] * 18,
        281: [ 0x0, 0x0 ] * 18,
        317: [ 0x0, 0x0 ] * 18,
        353: [ 34031, 17268,    0, 0,   20887, 15905,   45177, 15748,   13400, 15907,   33000, 17300] + [0, 0] * 5 + [33500, 17340,     41500, 17321,   41500, 15621] + [0, 0] * 4,
        389: [ 0x0, 0x0 ] * 18,
        425: [ 0x6661, 0x4249,  0, 0,   10500, 16991,   9210,  16999,   4233,  16840,   100,   16901] + [0, 0] * 5 + [1233,  16880,     1552,  16902,   10002, 15999] + [0, 0] * 4,
    },
    {
        1: [ 0x0106 ],
        2: [ 0x0002 ],
        3: [ 0x000A, 0x000B, 0x000C ],

        9:   [ 0x0002 ] * 6 + [ 0 ] * 5 + [ 0x0001 ] * 3 + [ 0 ] * 3 + [0x2],
        10:  [ 0x0, 0x0 ] * 18,
        65:  [ 0x0, 0x0 ] * 18,
        101: [ 0x0, 0x0 ] * 18,
        137: [ 0x0, 0x0 ] * 18,
        173: [ 0x0, 0x0 ] * 18,
        209: [ 0x0, 0x0 ] * 18,
        245: [ 0x0, 0x0 ] * 18,
        281: [ 0x0, 0x0 ] * 18,
        317: [ 0x0, 0x0 ] * 18,
        353: [ 34031, 17265,    0, 0,   20887, 15918,   45177, 15751,   13405, 15909,   33000, 17302,   50100, 15801,   40203, 17210 ] + [0, 0] * 3 + [33500, 17340,     0, 0,   41500, 15621] + [0, 0] * 2 + [ 40000, 15700 ],
        389: [ 0x0, 0x0 ] * 18,
        425: [ 0x6668, 0x4247,  0, 0,   10500, 16991,   9210,  16999,   4233,  16840,   100,   16901,   892,   16899,   523,   16788 ] + [0, 0] * 3 + [1233,  16880,     0, 0,   10002, 15999] + [0, 0] * 2 + [ 10010, 16700 ],
    },
]


_DEFAULT_REGISTERS_DICT = ROTATED_DATA[0]



DEFAULT_REGISTERS = ModbusSparseDataBlock(_DEFAULT_REGISTERS_DICT)


class PowerElec6Fake():
    """ Class that fakes a EcoAdapt POWER-ELEC-6 device that sends data through Modbus.

    This device can measure up to 6 three-phase or 18 single-phase outputs (or a combination
    of both).
    """
    def __init__(self, ip: str, rotate_time_s: int):
        """ Constructor of the class that fakes a POWER-ELEC-6.

        :param ip: The IP in which the faked device will communicate through Modbus.
        :param rotate_time_s: the time interval of data rotation in seconds.
        """
        self.ip = ip
        self.port = 502 # The manual says that it is port 502
        self.current_data_index = 0 # Index to keep track of current data in rotation
        self._rotate_time_s = rotate_time_s

        self._setup_modbus_server()

        # Start the timer to update registers every 50 seconds
        self._start_timer()

    def _setup_modbus_server(self):
        """ Sets up a simple Modbus TCP server with mock data.

        Modbus has 4 data types:
        1) Discrete inputs: read only booleans.
        2) Coils: read-write booleans.
        3) Input Registers: read only 16-bit word.
        4) Holding Registers: read-write 16-bit word.

        EcoAdapt Power Elec 6 exposes it's data as Input registers.
        """
        # The Power-Elec 6 provides 2 types of information via Modbus:
        # 1) general information of the meter
        # 2) information specific to a circuit (6 circuits with 3 channels each = 18 channels)

        store = ModbusSlaveContext(
            di=ModbusSparseDataBlock(),  # Discrete Inputs
            co=ModbusSparseDataBlock(),  # Coils
            hr=ModbusSparseDataBlock(),  # Holding Registers
            ir=DEFAULT_REGISTERS,        # Input Registers
        )

        self.context = ModbusServerContext(slaves=store, single=True)

        # Set up server identity information (optional)
        self.identity = ModbusDeviceIdentification()
        self.identity.VendorName = "MockModbusServer"
        self.identity.ProductCode = "MMS1"
        self.identity.VendorUrl = "https://www.eco-adapt.com/"
        self.identity.ProductName = "EcoAdapt POWER-ELEC-6"
        self.identity.ModelName = "POWER-ELEC-6"
        self.identity.MajorMinorRevision = "1.0"

        self._print_all_registers()

    def _print_all_registers(self):
        """ Print all the register values and addresses. """
        for key, val in _DEFAULT_REGISTERS_DICT.items():
            addr = key - 1 # ModbusSparseDataBlock keys have an offset of 1 on their addresses
            registers_in_obj = self.context[0].getValues(4, addr, count=len(val))
            log.info(f"ADDR = {addr:4}, DATA = {registers_in_obj}")

    def _update_registers(self):
        """ Update the data in the registers. """
        self.current_data_index = (self.current_data_index + 1) % len(ROTATED_DATA)
        log.info(f"Updating register values to set {self.current_data_index}...")
        for key, val in ROTATED_DATA[self.current_data_index].items():
            addr = key - 1 # ModbusSparseDataBlock keys have an offset of 1 on their addresses
            self.context[0].setValues(4, addr, val)
        self._print_all_registers()
        self._start_timer() # Restart the timer

    def _start_timer(self):
        """ Start a timer to update the registers every 50 seconds. """
        threading.Timer(self._rotate_time_s, self._update_registers).start()

    def start_modbus_server(self):
        """ Start modbus server in the configured port and ip. """
        # Start the Modbus TCP server on port 502
        log.info(f"Starting Mock Modbus TCP Server on {self.ip}:{self.port}...")
        StartTcpServer(self.context, identity=self.identity, address=(self.ip, self.port))


def parse_args():
    """ Parse arguments given to this CLI. """
    parser = argparse.ArgumentParser()

    parser.add_argument("--addr", required=True, type=str, help="The IP in which the Modbus server will be setup.")
    parser.add_argument("--rotate-time", required=True, type=int, help="The interval of time between data registers rotation.")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    power_elec = PowerElec6Fake(args.addr, args.rotate_time)

    power_elec.start_modbus_server()
