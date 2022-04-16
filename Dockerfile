FROM python:3.8-slim-bullseye
MAINTAINER Palo
WORKDIR /usr/src/app

# Core installation
RUN apt -y update --fix-missing && apt -y upgrade
RUN apt install -y git

# Dependencies installation
COPY requirements.txt .
RUN pip install --requirement requirements.txt

# Src files linking
COPY /src ./src

# Start of script
CMD ["python", "-u", "./src/main.py"]
