# sample_http testservice

A minimal Flask HTTP service that returns its hostname in JSON. Used for testing load balancing, sticky sessions, and traffic distribution across Kubernetes pod replicas.

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
| `ingress_dns`        | `testservice.local`  | Ingress hostname                |

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
