#!/usr/bin/env python

import requests
from loguru import logger
from time import sleep

POD_NAME = "alice-jobs-79468b8744-pjxbh"

while True:
    ENDPOINT = f"http://{POD_NAME}:8123"
    logger.debug("Test")

    try:
        requests.get(ENDPOINT, timeout=1)
    except requests.exceptions.Timeout:
        logger.error(f"Timed out query to {POD_NAME}")
        sleep(30)
        continue
    
    logger.debug(requests.text)
    sleep(30)
