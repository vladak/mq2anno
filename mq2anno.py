#!/usr/bin/env python3
"""
subscripe to MQTT events and turn them into Grafana annotations
"""

import argparse
import json
import logging
import sys

import requests

from logutil import LogLevelAction


def main():
    parser = argparse.ArgumentParser(
        description="convert MQTT events to Grafana annotations",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-H",
        "--headers",
        required=True,
        default="headers.json",
        help="JSON file with headers",
    )
    parser.add_argument(
        "-l",
        "--loglevel",
        action=LogLevelAction,
        help='Set log level (e.g. "ERROR")',
        default=logging.INFO,
    )
    parser.add_argument(
        "-U",
        dest="grafana_url",
        required=True,
        help="base URL for the Grafana server",
    )
    parser.add_argument(
        "mqtt_hostname",
        help="hostname of the MQTT broker",
    )
    parser.add_argument(
        "mqtt_port",
        help="port of the MQTT broker",
    )
    args = parser.parse_args()

    logging.basicConfig()
    logger = logging.getLogger(__package__)
    logger.setLevel(args.loglevel)
    logger.info("Running")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
