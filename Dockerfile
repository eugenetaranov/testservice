FROM python:3.10-slim

WORKDIR /app

COPY    python/ /app
RUN     pip3 install --upgrade pip && \
        pip3 install -r /app/requirements.txt

RUN     useradd -d /app app && \
        chown -R app /app
USER	app
ENV     FLASK_APP=main
EXPOSE 	8080/tcp

CMD     ["python3", "/app/main.py"]

