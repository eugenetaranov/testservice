# testservice

A collection of services and tools for testing load balancing, sticky sessions, and traffic distribution in Kubernetes.

## Services

### `services/sample_http`
A minimal Flask HTTP service that returns its hostname in JSON. Used for testing load balancing and sticky sessions across pod replicas. Deployed via raw K8s manifests or Terraform with configurable replicas, sticky cookies, and ingress hostname.

### `services/watchdog`
A Kubernetes pod health checker that periodically discovers pods by namespace/deployment and runs HTTP health checks against each pod's IP directly. Logs errors for unreachable or unhealthy pods. Configured via a YAML config file and environment variables.

## Test tools

### `test/test_service.py`
A load test script that polls a service URL and displays a live-updating table of request distribution across instances.

```bash
pip install -r test/requirements.txt
python3 test/test_service.py -u https://testservice.example.com
```

Options:
- `-u`, `--url` — URL to poll (required)
- `-i`, `--interval` — polling interval in seconds (default: 1)
- `-k`, `--insecure` — ignore SSL certificate errors

Features:
- Tracks request counts and percentage per instance
- Shows last-seen time per instance (yellow >60s, red >300s)
- Displays response status counters (2xx, 4xx, 5xx, err)
- Shows response headers including Set-Cookie
- Preserves cookies between requests for sticky session testing
