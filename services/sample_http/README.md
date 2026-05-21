# sample_http testservice

A minimal Flask HTTP service for testing Kubernetes behavior — load balancing, sticky sessions, traffic distribution, resource limits, graceful shutdown, and proxy/ingress behavior. Every response includes the pod hostname so you can see which replica served the request.

## API

### `GET /`
Returns JSON with the pod hostname and request path:
```json
{"hostname": "testservice-7887b6d6b4-vqcdr", "path": "/"}
```

### `GET /health`
Health check endpoint. Returns `200 Ok` when healthy, `503` when unhealthy. Controlled by `src/healthcheck_flag.txt` (`1` = healthy, `0` = unhealthy).

### `GET /delay?duration=<seconds>`
Sleeps for the requested duration (seconds, float-parseable), then returns JSON with the hostname, path, requested duration, and actual elapsed seconds. Useful for testing slow responses and timeouts. Returns `400` if `duration` is missing or not a number.

```bash
curl 'http://localhost:8080/delay?duration=2.5'
# {"hostname":"...","path":"/delay","duration":2.5,"elapsed":2.501}
```

### `ANY /echo`
Echoes request details as JSON: method, path, query, headers, body, client IP, and `X-Forwarded-*` / `X-Real-IP` headers. Useful for debugging ingress header rewriting, client-IP preservation, and proxy behavior. Accepts any HTTP method.

```bash
curl -X POST 'http://localhost:8080/echo?a=1&a=2' -d 'hello'
# {"hostname":"...","method":"POST","path":"/echo","query":{"a":["1","2"]},
#  "headers":{...},"remote_addr":"127.0.0.1","forwarded_for":null,...,
#  "body":"hello"}
```

### `GET /stream?chunks=<N>&interval=<ms>`
Server-Sent Events stream. Emits `chunks` events (default `10`) separated by `interval` milliseconds (default `500`). Each event carries the pod hostname, event index, and elapsed time. Useful for testing ingress idle timeouts, proxy buffering, long-lived connection drain behavior, and sticky-session persistence. For true bidirectional WebSocket testing (including `Upgrade` handling), see `/ws`.

```bash
curl -N 'http://localhost:8080/stream?chunks=5&interval=1000'
# data: {"hostname":"...","n":0,"elapsed":0.000}
# data: {"hostname":"...","n":1,"elapsed":1.001}
# ...
```

### `GET /ws` (WebSocket)
WebSocket endpoint. By default echoes any client frame back tagged with the pod hostname. With `interval=<ms>` (>0), also pushes periodic `{hostname, n, elapsed}` JSON frames; with `messages=<N>` (>0), closes after pushing `N` frames. Pass `echo=false` to disable echoing client messages. Useful for testing ingress `Upgrade: websocket` handling, proxy buffering on long-lived connections, drain behavior on pod termination, and sticky sessions across reconnects.

```bash
# server-push only
websocat 'ws://localhost:8080/ws?interval=1000&messages=5'
# {"hostname":"...","n":0,"elapsed":0.000}
# {"hostname":"...","n":1,"elapsed":1.001}
# ...

# echo
echo hello | websocat -n1 'ws://localhost:8080/ws'
# {"hostname":"...","echo":"hello"}
```

### `GET /memory?mb=<N>&hold=<seconds>`
Allocates `mb` MB of memory, touches every page so it's actually backed by RAM, holds for `hold` seconds (default `10`), then releases. Useful for testing container memory limits, OOMKilled behavior, and HPA memory-based scaling.

```bash
curl 'http://localhost:8080/memory?mb=64&hold=5'
# {"hostname":"...","mb":64,"hold":5,"allocated_bytes":67108864,"elapsed":5.01}
```

### `GET /cpu?duration=<seconds>&workers=<N>`
Burns CPU in a tight loop for `duration` seconds across `workers` threads (default `1`). Useful for testing CPU limits, throttling, and HPA CPU-based scaling. Note: Python's GIL limits CPU-bound threads to roughly one core total; use multiple pod replicas to push beyond.

```bash
curl 'http://localhost:8080/cpu?duration=10&workers=4'
# {"hostname":"...","duration":10,"workers":4,"elapsed":10.0,...}
```

### `GET /status/<code>`
Returns the requested HTTP status code (100–599). Useful for testing retry policies, circuit breakers, and ingress error handling. Status codes that disallow a body (204, 304) return empty; all others return `{hostname, status}`.

```bash
curl -i 'http://localhost:8080/status/418'
# HTTP/1.1 418 I'M A TEAPOT
# {"hostname":"...","status":418}
```

### `GET /flaky?fail_rate=<0..1>&status=<code>`
Fails a configurable fraction of requests (default `fail_rate=0.5`) with the configured status code (default `503`). Useful for retry, outlier-detection, and circuit-breaker experiments.

```bash
curl 'http://localhost:8080/flaky?fail_rate=0.3&status=502'
# {"hostname":"...","fail_rate":0.3,"failed":false}
```

### `GET /whoami?key=<key>`
Returns the pod index that *should* serve `key` under consistent hashing: `sha256(key) % REPLICAS`. The `REPLICAS` env var is wired up automatically in both the raw manifest (hardcoded, edit alongside `spec.replicas`) and the Terraform config (auto-tracks `var.replicas`). For StatefulSet-style hostnames (`name-<n>`), the responding pod's own index is also returned so the client can compare expected vs. actual.

```bash
curl 'http://localhost:8080/whoami?key=user-42'
# {"hostname":"...","key":"user-42","replicas":4,"expected_index":2,"this_index":null}
```

### `GET /crash`
Responds `{hostname, exiting: true}` and then exits the process (`os._exit(1)`) ~100ms later. Useful for testing pod restart behavior, readiness probe recovery, and in-flight connection handling on sudden death. Will trigger a pod restart per Kubernetes restart policy.

```bash
curl 'http://localhost:8080/crash'
# {"hostname":"...","exiting":true}
```

### `GET /payload?bytes=<N>`
Returns `N` bytes of payload (`application/octet-stream`, value `0x41`). The pod hostname is returned in the `X-Hostname` header. Useful for testing ingress/proxy buffer thresholds, MTU effects, and bandwidth-shaped behavior.

```bash
curl -o /dev/null -w '%{size_download}\n' 'http://localhost:8080/payload?bytes=1048576'
# 1048576
```

## Build

```bash
docker build -t eugenetaranov/testservice:latest .
```

## Kubernetes deployment

### Using raw manifests
```bash
kubectl apply -f k8s/testservice.yaml
```

### Using Terraform
```bash
cd terraform
terraform init
terraform apply -var="cluster_name=my-cluster" -var="ingress_dns=testservice.example.com"
```

#### Terraform variables

| Variable            | Default              | Description                    |
|---------------------|----------------------|--------------------------------|
| `cluster_name`      | `""`                 | EKS cluster name               |
| `namespace`          | `test`               | Kubernetes namespace            |
| `replicas`           | `1`                  | Number of pod replicas          |
| `stickiness_enabled` | `false`              | Enable Traefik sticky cookies   |
| `stickiness_maxage`  | `30`                 | Sticky cookie max age (seconds) |
| `ingress_dns`        | `testservice.test`   | Ingress hostname                |

## Sticky sessions

When `stickiness_enabled = true`, the Terraform config adds Traefik annotations to the Service for cookie-based sticky sessions (cookie name: `testservice`, max age: 30s).

## Pre-stop hook

The pod runs a pre-stop hook (`src/hooks/pre_stop.sh`) that sleeps for 300 seconds, allowing in-flight requests to complete during graceful shutdown. The `terminationGracePeriodSeconds` is set to 120s.

## Load test tool

Use `test_service.py` (in the repo root) to monitor request distribution across replicas:

```bash
pip install -r requirements.txt
python3 test_service.py -u https://testservice.example.com
```

Options:
- `-u`, `--url` — URL to poll (required)
- `-i`, `--interval` — polling interval in seconds (default: 1)
- `-k`, `--insecure` — ignore SSL certificate errors

The tool displays a live table showing request counts per instance, percentage distribution, and last-seen time. Rows turn yellow (>60s) or red (>300s) if an instance hasn't been seen recently.
