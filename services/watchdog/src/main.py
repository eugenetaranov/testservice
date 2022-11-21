#!/usr/bin/env python

from loguru import logger
from time import sleep


while True:
    logger.debug("That's it, beautiful and simple logging!")
    sleep(10)
