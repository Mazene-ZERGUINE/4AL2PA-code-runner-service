#!/bin/bash

# Check if the Docker image exists
if [[ "$(docker images -q code_runner:latest 2> /dev/null)" == "" ]]; then
    echo "Docker image does not exist. Building the image..."
    docker build -f Dockerfile -t code_runner:latest .
else
    echo "Docker image already exists. Skipping build."
fi

# Run the production scripts
./run_prod.sh

./run_celeryapp_prod.sh