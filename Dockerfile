FROM python:3.8-slim-bullseye
MAINTAINER Palo
WORKDIR /usr/src/app

# Core installation
RUN apt -y update --fix-missing && apt -y upgrade
RUN apt install -y git

# Project files linking
COPY requirements.txt .
COPY /src ./src

# Dependencies installation
RUN pip install --no-cache-dir -r requirements.txt

# Start of script
CMD ["python", "-u", "./src/main.py"]
