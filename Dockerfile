FROM ubuntu:latest

# Install Node.js
RUN apt-get update && \
    apt-get install -y nodejs npm python3 python3-pip

# Set up work directory
WORKDIR /app
