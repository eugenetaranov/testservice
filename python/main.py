#!/usr/bin/env python

from flask import Flask
import socket

app = Flask(__name__)


@app.route("/health")
def health():
    with open("healthcheck_flag.txt", "r") as f:
        try:
            healthcheck_flag = int(f.readline())
        except:
            healthcheck_flag = False

    if healthcheck_flag:
        return "Ok", 200
    else:
        return "", 503


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    res = {
        "hostname": socket.gethostname(),
        "path": f"/{path}",
    }
    return res


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
