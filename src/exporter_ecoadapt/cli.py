import logging
import argparse
import asyncio
from exporter_ecoadapt.exporter_ecoadapt import ExporterEcoAdapt


FORMAT = (
    "%(asctime)-15s %(threadName)-15s "
    "%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
)

logging.basicConfig(format=FORMAT, level=logging.INFO)

log = logging.getLogger(__name__)


def parse_args():
    """ Parse arguments given to this CLI. """
    parser = argparse.ArgumentParser()

    cloud_group = parser.add_argument_group("cloud", "Cloud connection settings")
    cloud_group.add_argument("--addr", required=True, type=str, help="The address of the cloud server to send the data to.")

    modbus_group = parser.add_argument_group("modbus", "Modbus connection settings")
    modbus_group.add_argument("--port", default=502, type=int, help="The Modbus port used to listen data from.")
    modbus_group.add_argument("--addr", required=True, type=str, help="The Modbus IP address used to listen data from.")

    parser.add_argument("--time-interval", default=10, type=int, help="Time interval between each read to the device.")

    return parser.parse_args()


async def cli():
    """ Main Command Line Interface tool entrypoint. """
    args = parse_args()

    log.info("Starting exporter-ecoadapt CLI!")

    exporter_eco_adapt = ExporterEcoAdapt(
        cloud_url = args.cloud.addr,
        modbus_addres = args.modbus.addr,
        modbus_port = args.modbus.port,
        read_time_interval_s = args.read_time_interval_s
    )

    await exporter_eco_adapt.run()


if __name__ == "__main__":
    asyncio.run(cli())
