#!/usr/bin/env python

import requests
from kubernetes import client, config
from loguru import logger
from time import sleep

POD_NAME = "alice-jobs-79468b8744-pjxbh"


def main():
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
