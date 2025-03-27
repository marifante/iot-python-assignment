import argparse
import logging

from pymodbus.server.sync import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext


FORMAT = (
    "%(asctime)-15s %(threadName)-15s "
    "%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
)

logging.basicConfig(format=FORMAT, level=logging.INFO)

log = logging.getLogger(__name__)


class EcoAdaptPowerElecFake():
    """ Class that fakes a EcoAdapt POWER-ELEC-6 device that sends data through Modbus. """
    def __init__(self, ip: str):
        """ Constructor of the class that fakes a POWER-ELEC-6.

        :param ip: The IP in which the faked device will communicate through Modbus.
        """
        self.ip = ip
        self.port = 502 # The manual says that it is port 502

        self._setup_modbus_server()

    def _setup_modbus_server(self):
        """ Sets up a simple Modbus TCP server with mock data."""
        # Define a data block with initial mock values (e.g., holding registers)
        store = ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0, [0] * 100),  # Discrete Inputs
            co=ModbusSequentialDataBlock(0, [0] * 100),  # Coils
            hr=ModbusSequentialDataBlock(0, [10, 20, 30, 40, 50]),  # Holding Registers
            ir=ModbusSequentialDataBlock(0, [100, 200, 300, 400, 500])  # Input Registers
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
