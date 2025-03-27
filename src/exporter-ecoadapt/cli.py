import logging
import argparse
from exporter_ecoadapt import


FORMAT = (
    "%(asctime)-15s %(threadName)-15s "
    "%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
)

logging.basicConfig(format=FORMAT, level=logging.INFO)

log = logging.getLogger(__name__)


def parse_args():
    """ Parse arguments given to this CLI. """
    parser = argparse.ArgumentParser()

    modbus_group = parser.add_argument_group("Modbus", "Modbus connection settings")
    modbus_group.add_argument("--port", default=502, type=int, help="The Modbus port used to listen data from.")
    modbus_group.add_argument("--addr", default="169.254.20.1", type=str, help="The Modbus IP address used to listen data from.")
    modbus_group.add_argument("--unit", default=0x1, type=int, help="Modbus unit number.")

    return parser.parse_args()


def cli():
    """ Main Command Line Interface tool entrypoint. """
    args = parse_args()

    log.info("Starting exporter-ecoadapt CLI!")


if __name__ == "__main__":
    cli()
