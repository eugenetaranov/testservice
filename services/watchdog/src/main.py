#!/usr/bin/env python

import requests
from loguru import logger
from time import sleep

ENDPOINT = "http://alice-jobs-79468b8744-pjxbh:8123"

while True:
    logger.debug("Test")
    requests.get(ENDPOINT)
    logger.debug(requests.text)
    sleep(30)
