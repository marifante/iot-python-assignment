import argparse
import logging

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


DEFAULT_REGISTERS = ModbusSparseDataBlock(
    {
        # General information
        0: [ 0x0106 ], # Software Version
        1: [ 0x0002 ], # Modbus table Version
        2: [ 0x000A, 0x000B, 0x000C ], # MAC address

        # Information per circuit (6 circuits, 3 channels/circuit = 18 channels)
        8:   [ 0x0002 ] * 18,          # Circuit configuration (from 8 to 25, 16-bit word per channel)
        28:  [ 0x0, 0x0 ] * 18,        # [kWh] Active energy import index (from 28 to 63, float32 per channel)
        64:  [ 0x0, 0x0 ] * 18,        # [kVArh] Reactive energy import index (from 64 to 99, float32 per channel)
        100: [ 0x0, 0x0 ] * 18,        # [kWh] Active energy export index (from 100 to 135, float32 per channel)
        136: [ 0x0, 0x0 ] * 18,        # [kVArh] Reactive energy export index (from 136 to 171, float32 per channel)
        172: [ 0x0, 0x0 ] * 18,        # [W] Active power (from 172 to 207, float32 per channel)
        208: [ 0x0, 0x0 ] * 18,        # [Var] Reactive power (from 208 to 243, float32 per channel)
        244: [ 0x0, 0x0 ] * 18,        # Power factor (from 244 to 279, float32 per channel)
        280: [ 0x0, 0x0 ] * 18,        # [A] RMS current (from 280 to 315, float32 per channel)
        316: [ 0x0, 0x0 ] * 18,        # [A] RMS current 1 min average (from 316 to 351, float32 per channel)
        352: [ 0x4365, 0xE3D7 ] * 18,  # [V] RMS voltage (from 352 to 387, float32 per channel), 0x4365E3D7 = 229.89 V
        388: [ 0x0, 0x0 ] * 18,        # [V] RMS voltage 1 min average (from 388 to 423, float32 per channel)
        424: [ 0x4248, 0x6666 ] * 18,  # [Hz] Frequency (from 424 to 459, float32 per channel), 0x42486666 = 50.1 Hz
    }
)


class EcoAdaptPowerElecFake():
    """ Class that fakes a EcoAdapt POWER-ELEC-6 device that sends data through Modbus.

    This device can measure up to 6 three-phase or 18 single-phase outputs (or a combination
    of both).
    """
    def __init__(self, ip: str):
        """ Constructor of the class that fakes a POWER-ELEC-6.

        :param ip: The IP in which the faked device will communicate through Modbus.
        """
        self.ip = ip
        self.port = 502 # The manual says that it is port 502

        self._setup_modbus_server()

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

    def start_modbus_server(self):
        """ Start modbus server in the configured port and ip. """
        # Start the Modbus TCP server on port 502
        log.info(f"Starting Mock Modbus TCP Server on {self.ip}:{self.port}...")
        StartTcpServer(self.context, identity=self.identity, address=(self.ip, self.port))


def parse_args():
    """ Parse arguments given to this CLI. """
    parser = argparse.ArgumentParser()

    parser.add_argument("--addr", required=True, type=str, help="The IP in which the Modbus server will be setup.")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    power_elec = EcoAdaptPowerElecFake(args.addr)

    power_elec.start_modbus_server()
