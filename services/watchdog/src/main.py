#!/usr/bin/env python

import requests
import os
import yaml
from kubernetes import client, config
from loguru import logger
from yaml.loader import SafeLoader
from time import sleep


def main():
    config_path = os.getenv("CONFIG_FILE")
    with open(config_path) as f:
        cfg = yaml.load(f, Loader=SafeLoader)
    
    logger.debug(cfg)

    config.load_incluster_config()
    v1 = client.CoreV1Api()

    while True:
        ret = v1.list_pod_for_all_namespaces(watch=False)
        for i in ret.items:
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
