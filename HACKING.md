# HACKING

In this notes you can find the reasoning behind to solve this assignment.

1) Define and analyze the problem.

In a grasp, I need to develop a service that reads data from Modbus from a device and exports it to a cloud server.
The application needs to be deployed to sensorfact bridges using ssh & scp.

The application shall:
* read the voltage and frequency from the sensor (around 230 V / 50 V) using modbus
* send those values to the server periodically
* be installable through ssh & scp

2) Prepare my work environment.

2.1) As the deliverable will be a Python application, I'll start clean from the beginning packaging with pip. This will make the delivery process easier. Here I'll create a `setup.py` to install it as a library and to install a CLI to use it.

2.2) I'll package in a simple bash script the steps needed to setup an environment. That script is in `scripts/setup.sh` and to use it we need to source it: `source scripts/setup.sh`.

3) How to test it?

3.1) First of all, we need to make unit-tests for our python application. This can be easily done with pytest and unittest.

3.2) In order to make an integration test for this application, I'll create a "fake" Eco-Adapt Power Elect using python. Since Eco-Adapt Power Elect uses ModBus over TCP, we can create a fake ModBus server that holds hardcoded data and communicate our application with this fake server. So, I'll make a "fake" Eco-Adapt Power Elect: `dev/ecoadapt_power_elec_fake.py`.

To setup this test I'll use docker compose. I'll run 3 services there:
* one mocking the cloud server (`dev/server.py`, `docker/Dockerfile.cloud_server`)
* another one faking the Eco Adapt Power Elec (`dev/ecoadapt_power_elec_fake.py`, `docker/Dockerfile.ecoadapt_power_elec_fake`)
* and our application (`src/exporter-ecoadapt`, `docker/Dockerfile.exporter_ecoadapt`)

All those services will communicate using an internal network that will be setup by docker compose. Our application will read the data from the fake Eco Adapt using ModBus over TCP and then it will send it to the cloud server using a websocket.

To run the integration test we shall only run: `docker-compose up --build` from the root of the repository.

3) Application layout.



4) Bonus (CI/CD): Since I love to work with automated tests, I'll create a small GitHub actions pipeline to run the unit-tests of the application and some integration tests using the mocked cloud server.


