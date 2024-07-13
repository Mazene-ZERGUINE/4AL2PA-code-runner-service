#!/bin/bash

docker build -f Dockerfile -t code_runner_service-api:latest .

./run_prod.sh

./run_celeryapp.sh