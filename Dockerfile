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

# Setup of python environment path, else docker has issue with import of modules
ENV PYTHONPATH "${PYTHONPATH}:/usr/src/app"

# Start of the script, always keep as last command
CMD ["python", "-u", "/usr/src/app/src/main.py"]
