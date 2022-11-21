#!/usr/bin/env python

import requests
import os
import yaml
from kubernetes import client, config
from loguru import logger
from yaml.loader import SafeLoader
from time import sleep


class K8S:
    def __init__(self):
        config.load_incluster_config()
        self.v1 = client.CoreV1Api()

    def get_pods(self, namespaces=[]) -> object:
        pods = []
        for namespace in namespaces:
            res = self.v1.list_namespaced_pod(namespace=namespace, watch=False)
            pods.extend(res.items)
        
        return pods


def main():
    config_path = os.getenv("CONFIG_FILE")
    with open(config_path) as f:
        cfg = yaml.load(f, Loader=SafeLoader)
    
    logger.debug(cfg)

    # config.load_incluster_config()
    # v1 = client.CoreV1Api()

    k = K8S()

    while True:
        pods = k.get_pods(namespaces=cfg["namespaces"])
        for i in pods:
            logger.info(f"{i.metadata.namespace}/{i.metadata.name} {i.status.pod_ip}")

        sleep(60)


if __name__ == '__main__':
    main()

# while True:
#     ENDPOINT = f"http://{POD_NAME}:8123"

#     try:
#         requests.get(ENDPOINT, timeout=1)
#     except requests.exceptions.Timeout:
#         logger.error(f"Timed out query to {POD_NAME}")
#         sleep(30)
#         continue

#     logger.debug(requests.text)
#     sleep(30)
