# This file is used to containerize our application
# It specifies which files to copy into the container, which
# packages to install, and which command to run for the application.

# Build using: docker build -t <image-name> .
# Run using: docker run --rm --env-file .env -p 8081:8081 <image-name>

# Use an official Python runtime as a parent image
FROM python:3.12-slim

RUN apt-get update && apt-get install -y gcc python3-dev

# Set the working directory to /app
WORKDIR /app

# Copy dependencies into the container at /app
COPY pyproject.toml /app

# Install depencies only, avoids re-installing all dependencies when the code changes
RUN pip install .

# Now copy the code into the container at /app
COPY /src /app/src

# Install our project only when the code changes, to speed up the build
RUN pip install .

# Run app with streamlit
# TODO: Fill me in! Add the path to our app for streamlit to run
CMD ["streamlit", "run", "<path_to_our_app", "--server.port", "8081"]
