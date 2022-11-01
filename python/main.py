#!/usr/bin/env python

from flask import Flask
import socket

app = Flask(__name__)

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    res = {
        "hostname": socket.gethostname(),
        "path": f"/{path}",
    }
    return res


if __name__ == "__main__":
    app.run()
