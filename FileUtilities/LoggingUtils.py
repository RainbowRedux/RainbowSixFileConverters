"""Provides some extra features for logging"""

import pprint
import logging

def log_pprint(data: str, loglevel=logging.INFO):
    """Pretty prints data to individual lines in the logging module"""
    for line in pprint.pformat(data).split('\n'):
        logging.log(loglevel, line)
