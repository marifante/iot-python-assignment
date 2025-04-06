"""
Command Line Interface used to launch exporter_ecoadapt application.
"""
import logging
import argparse
import asyncio
from exporter_ecoadapt.exporter_ecoadapt import ExporterEcoAdapt


FORMAT = (
    "%(asctime)-15s %(threadName)-15s "
    "%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
)


log = logging.getLogger(__name__)


def parse_args():
    """ Parse arguments given to this CLI. """
    parser = argparse.ArgumentParser(description="Application used to read data from Power Elec 6 devices and export it to a cloud server.")

    cloud_group = parser.add_argument_group("cloud", "Cloud connection settings")
    cloud_group.add_argument("--cloud-addr", required=True, type=str, help="The address of the cloud server to send the data to.")
    cloud_group.add_argument("--cloud-port", required=True, type=int, help="The port of the cloud server to send the data to.")

    modbus_group = parser.add_argument_group("modbus", "Modbus connection settings")
    modbus_group.add_argument("--modbus-port", default=502, type=int, help="The Modbus port used to listen data from.")
    modbus_group.add_argument("--modbus-addr", required=True, type=str, help="The Modbus IP address used to listen data from.")

    parser.add_argument("--time-interval", default=60, type=int, help="Time interval between each read to the sensor.")
    parser.add_argument("--log-level", default="INFO", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help="Set logging level")

    return parser.parse_args()


async def cli():
    """ Main Command Line Interface tool entrypoint. """
    args = parse_args()

    logging.basicConfig(format=FORMAT, level=args.log_level)

    log.info("Starting exporter-ecoadapt CLI!")

    loop = asyncio.get_running_loop()

    exporter_eco_adapt = ExporterEcoAdapt(
        cloud_url = args.cloud_addr,
        cloud_port = args.cloud_port,
        modbus_address = args.modbus_addr,
        modbus_port = args.modbus_port,
        read_time_interval_s = args.time_interval,
        loop=loop
    )

    await exporter_eco_adapt.run()


def main():
    """ Synchronous wrapper to run the async CLI. """
    asyncio.run(cli())


if __name__ == "__main__":
    main()
