#!/usr/bin/env python

import requests
import os
import yaml
from kubernetes import client, config
from loguru import logger
from yaml.loader import SafeLoader
from time import sleep
from dataclasses import dataclass


SLEEP = 30


@dataclass
class Pod:
    name: str
    namespace: str
    deployment: str
    ip: str


class K8S:
    def __init__(self, incluster=False):
        if incluster:
            config.load_incluster_config()
        else:
            config.load_config()

        self.core_client = client.CoreV1Api()
        self.api_client = client.AppsV1Api()

    def get_pods(self, namespaces=[], deployments=[]) -> object:
        pods_all = []
        pods_filtered = []

        for namespace in namespaces:
            try:
                res = self.core_client.list_namespaced_pod(
                    namespace=namespace, timeout_seconds=2, watch=False
                )
            except:
                logger.error(f"Timed out listing pods")
                return None

            pods_all.extend(res.items)

        for i in pods_all:
            pod = Pod(
                name=i.metadata.name,
                namespace=i.metadata.namespace,
                deployment="",
                ip=i.status.pod_ip,
            )

            if "name" in i.metadata.labels:
                pod.deployment = i.metadata.labels["name"]

            if deployments:
                if pod.deployment not in deployments:
                    continue

            logger.debug(
                f"Discovered {pod.namespace}/{pod.name}, deployment {pod.deployment} with ip {pod.ip}"
            )
            pods_filtered.append(pod)

        return pods_filtered


def run_healthcheck(
    namespace: str, pod_name: str, proto: str, ip: str, port: int
) -> bool:
    url = f"{proto}://{ip}:{port}"

    try:
        res = requests.get(url, timeout=1)
    except requests.exceptions.Timeout:
        logger.error(f"Timed out querying {namespace}/{pod_name} at {url}")
        return

    if res.ok:
        logger.debug(f"{namespace}/{pod_name} at {url}: {res.status_code}")
    else:
        logger.error(
            f"Error querying {namespace}/{pod_name} at {url}: {res.status_code}"
        )


def main():
    config_path = os.getenv("CONFIG_FILE")
    with open(config_path) as f:
        cfg = yaml.load(f, Loader=SafeLoader)

    logger.debug(cfg)

    if "KUBERNETES_SERVICE_HOST" in os.environ:
        k = K8S(incluster=True)
    else:
        k = K8S()

    while True:
        pods = k.get_pods(namespaces=["int0"], deployments=["alice-jobs"])
        for pod in pods:
            run_healthcheck(
                namespace=pod.namespace,
                pod_name=pod.name,
                proto="http",
                ip=pod.ip,
                port=cfg["port"],
            )

        sleep(SLEEP)


if __name__ == "__main__":
    main()
