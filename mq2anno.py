#!/usr/bin/env python3
"""
subscribe to MQTT events and turn them into Grafana annotations
"""

import argparse
import copy
import json
import logging
import sys
import time

import paho.mqtt.client as mqtt
import requests

from logutil import LogLevelAction


class FatalError(Exception):
    """
    exception that should prompt clean exit
    """


# pylint: disable=unused-argument
def on_connect(client, userdata, flags, ret_code, properties):
    """
    called on MQTT connect
    :param client:
    :param userdata:
    :param flags:
    :param ret_code:
    :return:
    """
    logger = logging.getLogger(__name__)

    if ret_code == 0:
        logger.info("Connected to MQTT broker")
    else:
        logger.error(f"Connect to MQTT broker failed with code {ret_code}")
        raise FatalError("cannot connect to MQTT broker")

    logger.info(f"Subscribing to topic {userdata.topic}")
    client.subscribe(userdata.topic)


# pylint: disable=unused-argument
def on_message(client, userdata, msg):
    """
    called on MQTT message received
    :param client:
    :param userdata:
    :param msg:
    :return:
    """
    logger = logging.getLogger(__name__)

    logger.debug(f"received: {msg.topic} {msg.payload}")

    create_annotation(userdata, msg.payload.decode("utf-8)"))


def create_annotation(userdata, tag):
    """
    :param userdata: Userdata instance
    :param tag: string tag
    """

    logger = logging.getLogger(__name__)

    payload = copy.deepcopy(userdata.payload)
    time_start = int(time.time() * 1000)
    payload["time"] = int(time_start)
    payload["timeEnd"] = int(time_start) + 500
    if not payload.get("tags"):
        payload["tags"] = []
    payload["tags"].append(tag)
    url = userdata.grafana_url + "/api/annotations"
    payload_str = json.dumps(payload)
    logger.debug(f"posting {payload_str} with {userdata.headers} to {url}")
    try:
        response = requests.post(
            url, data=payload_str, headers=userdata.headers, timeout=3
        )
        if response.status_code != 200:
            logger.error(f"Failed to post {payload_str} to {url}: {response.text}")
    except requests.exceptions.ConnectionError as exc:
        logger.error(f"failed to post: {exc}")


# pylint: disable=too-few-public-methods
class Userdata:
    """
    configuration for MQTT handling
    """

    def __init__(self, topic, grafana_url, payload, headers):
        """
        :param topic: MQTT topic
        :param grafana_url: Grafana base URL
        :param payload: dictionary template for the payload to send to Grafana
        :param headers: HTTP headers
        """
        self.topic = topic
        self.grafana_url = grafana_url
        self.payload = payload
        self.headers = headers


def main():
    """
    main CLI
    """
    parser = argparse.ArgumentParser(
        description="convert MQTT events to Grafana annotations",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-H",
        "--headers",
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
        "-t",
        "--topic",
        required=True,
        help="MQTT topic to subscribe to",
    )
    parser.add_argument(
        "-p",
        "--payload",
        default="payload.json",
        help="JSON file with Grafana payload template",
    )
    parser.add_argument(
        "mqtt_hostname",
        help="hostname of the MQTT broker",
    )
    parser.add_argument(
        "mqtt_port",
        type=int,
        help="port of the MQTT broker",
    )
    args = parser.parse_args()

    logging.basicConfig()
    logger = logging.getLogger(__package__)
    logger.setLevel(args.loglevel)
    logger.info("Running")

    with open(args.headers, encoding="utf-8") as file_handle:
        headers = json.load(file_handle)
        logger.debug(f"Got headers: {headers}")

    with open(args.payload, encoding="utf-8") as file_handle:
        payload = json.load(file_handle)
        logger.debug(f"Got payload: {payload}")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    user_data = Userdata(args.topic, args.grafana_url, payload, headers)
    client.user_data_set(user_data)
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        keep_alive = 60
        client.connect(args.mqtt_hostname, args.mqtt_port, keep_alive)
    except OSError as exc:
        raise FatalError from exc
    client.loop_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except FatalError as fatal_exc:
        logging.getLogger(__name__).fatal(f"cannot continue: {fatal_exc}")
        sys.exit(1)
