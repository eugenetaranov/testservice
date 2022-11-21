FROM python:3.10-slim

ENV TINI_VERSION v0.19.0
ENV     DEBIAN_FRONTEND=noninteractive

WORKDIR /app

ADD     https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
COPY    src/ /app
RUN     chmod +x /tini
RUN     apt update && \
        apt install -y curl vim && \
        pip3 install --upgrade pip && \
        pip3 install -r /app/requirements.txt

RUN     useradd -d /app app && \
        chown -R app /app
USER	app
ENTRYPOINT ["/tini", "--"]
CMD     ["python3", "/app/main.py"]
