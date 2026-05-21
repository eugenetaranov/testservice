#!/usr/bin/env python

from flask import Flask, request, Response, stream_with_context
import hashlib
import os
import random
import re
import socket
import sys
import threading
import time
from datetime import datetime

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
        ts = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
        print(f"{ts} healtcheck failed", file=sys.stderr)
        return "", 503


@app.route("/delay")
def delay():
    try:
        duration = float(request.args.get("duration", ""))
    except ValueError:
        return {"error": "invalid or missing 'duration' query arg"}, 400
    start = time.monotonic()
    time.sleep(max(0.0, duration))
    return {
        "hostname": socket.gethostname(),
        "path": "/delay",
        "duration": duration,
        "elapsed": time.monotonic() - start,
    }


@app.route("/echo", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
def echo():
    return {
        "hostname": socket.gethostname(),
        "method": request.method,
        "path": request.path,
        "query": request.args.to_dict(flat=False),
        "headers": dict(request.headers),
        "remote_addr": request.remote_addr,
        "forwarded_for": request.headers.get("X-Forwarded-For"),
        "forwarded_proto": request.headers.get("X-Forwarded-Proto"),
        "forwarded_host": request.headers.get("X-Forwarded-Host"),
        "real_ip": request.headers.get("X-Real-IP"),
        "body": request.get_data(as_text=True),
    }


@app.route("/stream")
def stream():
    try:
        chunks = int(request.args.get("chunks", "10"))
        interval_ms = int(request.args.get("interval", "500"))
    except ValueError:
        return {"error": "invalid 'chunks' or 'interval'"}, 400

    hostname = socket.gethostname()
    interval = max(0.0, interval_ms / 1000.0)

    def generate():
        start = time.monotonic()
        for i in range(chunks):
            payload = (
                f'{{"hostname":"{hostname}","n":{i},'
                f'"elapsed":{time.monotonic() - start:.3f}}}'
            )
            yield f"data: {payload}\n\n"
            if i < chunks - 1:
                time.sleep(interval)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/memory")
def memory():
    try:
        mb = int(request.args.get("mb", ""))
        hold = float(request.args.get("hold", "10"))
    except ValueError:
        return {"error": "invalid or missing 'mb'/'hold'"}, 400
    start = time.monotonic()
    buf = bytearray(mb * 1024 * 1024)
    # touch pages so the kernel actually backs them with RAM
    for i in range(0, len(buf), 4096):
        buf[i] = 1
    time.sleep(max(0.0, hold))
    allocated = len(buf)
    del buf
    return {
        "hostname": socket.gethostname(),
        "mb": mb,
        "hold": hold,
        "allocated_bytes": allocated,
        "elapsed": time.monotonic() - start,
    }


def _burn_cpu(end_at):
    while time.monotonic() < end_at:
        pass


@app.route("/cpu")
def cpu():
    try:
        duration = float(request.args.get("duration", ""))
        workers = int(request.args.get("workers", "1"))
    except ValueError:
        return {"error": "invalid or missing 'duration'/'workers'"}, 400
    workers = max(1, workers)
    start = time.monotonic()
    end_at = start + max(0.0, duration)
    threads = [threading.Thread(target=_burn_cpu, args=(end_at,)) for _ in range(workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return {
        "hostname": socket.gethostname(),
        "duration": duration,
        "workers": workers,
        "elapsed": time.monotonic() - start,
        "note": "Python GIL limits CPU-bound threads to ~1 core total",
    }


@app.route("/status/<int:code>")
def status(code):
    if code < 100 or code > 599:
        return {"error": "code must be 100-599"}, 400
    # 204/304 disallow message body
    if code in (204, 304):
        return "", code
    return (
        {"hostname": socket.gethostname(), "status": code},
        code,
    )


@app.route("/flaky")
def flaky():
    try:
        fail_rate = float(request.args.get("fail_rate", "0.5"))
        fail_status = int(request.args.get("status", "503"))
    except ValueError:
        return {"error": "invalid 'fail_rate' or 'status'"}, 400
    fail_rate = min(1.0, max(0.0, fail_rate))
    failed = random.random() < fail_rate
    body = {
        "hostname": socket.gethostname(),
        "fail_rate": fail_rate,
        "failed": failed,
    }
    return (body, fail_status if failed else 200)


def _pod_index_from_hostname(hostname):
    m = re.search(r"-(\d+)$", hostname)
    return int(m.group(1)) if m else None


@app.route("/whoami")
def whoami():
    key = request.args.get("key", "")
    if not key:
        return {"error": "missing 'key' query arg"}, 400
    try:
        replicas = int(os.environ.get("REPLICAS", "1"))
    except ValueError:
        replicas = 1
    replicas = max(1, replicas)
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    expected_index = int(digest, 16) % replicas
    hostname = socket.gethostname()
    return {
        "hostname": hostname,
        "key": key,
        "replicas": replicas,
        "expected_index": expected_index,
        "this_index": _pod_index_from_hostname(hostname),
    }


@app.route("/crash")
def crash():
    def _exit_soon():
        time.sleep(0.1)
        os._exit(1)
    threading.Thread(target=_exit_soon, daemon=True).start()
    return {"hostname": socket.gethostname(), "exiting": True}


@app.route("/payload")
def payload():
    try:
        nbytes = int(request.args.get("bytes", ""))
    except ValueError:
        return {"error": "invalid or missing 'bytes'"}, 400
    nbytes = max(0, nbytes)
    return Response(
        b"A" * nbytes,
        mimetype="application/octet-stream",
        headers={"X-Hostname": socket.gethostname()},
    )


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
