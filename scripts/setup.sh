#!/bin/bash

VENV_NAME="venv"

rm -rf ${VENV_NAME} >/dev/null 2>&1

python3 -m venv ./${VENV_NAME}

source ./${VENV_NAME}/bin/activate

pip3 install -e .

pip3 install -r requirements-dev.txt

echo "Virtual environment created with required dependencies"
