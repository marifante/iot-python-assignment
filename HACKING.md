# HACKING

In this notes you can find the reasoning behind to solve this assignment.

1) Define and analyze the problem.

In a grasp, I need to develop a service that reads data from Modbus from a device and exports it to a cloud server.

2) Prepare my work environment.

2.1) As the deliverable will be a Python application. I'll start clean from the beginning packaging with pip. Here I'll create a `setup.py` to install it as a library and to install a CLI to use it.

2.2) Since I'll need to test it, one of the better ways will be using docker compose. I'll run 2 services there, one will be mocking the "cloud" server and the other one will be our data gatherer application. Here I'll create 2 dockerfiles: `Dockerfile.exporter_ecoadapt` to have a container with our application "reading" data from modbus and exporting it through a websocket and `Dockerfile.cloud_server` to receive the data sent by the exporter and print it through stdout. Then, I'll create a `docker-compose.yml` to launch the 2 containers.

2.3) Since I love to work with automated tests, I'll create a small GitHub actions pipeline to run the unit-tests of the application and some integration tests using the mocked cloud server.


