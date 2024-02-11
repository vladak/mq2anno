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
from json import JSONDecodeError

import paho.mqtt.client as mqtt
import requests

from logutil import LogLevelAction


class FatalError(Exception):
    """
    exception that should lead to exit of the program with non-zero code
    """

    def __init__(self, message):
        super().__init__(message)


# pylint: disable=unused-argument
def on_connect(client, userdata, flags, ret_code, properties):
    """
    called on MQTT connect
    """
    logger = logging.getLogger(__name__)

    if ret_code == 0:
        logger.info("Connected to MQTT broker")
    else:
        logger.error(f"Connect to MQTT broker failed with code {ret_code}")
        raise FatalError("cannot connect to MQTT broker")


# pylint: disable=unused-argument
def on_message(client, userdata, msg):
    """
    called on MQTT message received
    :param client: MQTT object
    :param userdata: Userdata instance
    :param msg: message structure
    :return:
    """
    logger = logging.getLogger(__name__)

    logger.debug(f"received: {msg.topic} {msg.payload}")

    topic_config = userdata.topic_config

    if msg.topic not in topic_config.keys():
        logger.warning(f"topic {msg.topic} configuration not found")
        return

    try:
        p = json.loads(msg.payload)
        if not p.get("annotation"):
            logger.warning(f"no 'annotation' key in payload {msg.payload}")
            return

        tags = p.get("tags")
        if tags is None and isinstance(tags, list):
            try:
                create_annotation(userdata, msg.topic, tags)
            except ValueError as e:
                logger.error(f"cannot create annotation for {msg.topic}: {e}")
        else:
            logger.warning(f"{msg.payload} does not contain list of tags")
    except JSONDecodeError as e:
        logger.warning(f"cannot decode '{msg.payload}' as JSON: {e}")


def create_annotation(userdata, topic, tags):
    """
    Create Grafana annotation per
    https://grafana.com/docs/grafana/latest/developers/http_api/annotations/#create-annotation
    :param userdata: Userdata object
    :param topic: MQTT topic
    :param tags: list of tags to add to the template
    """

    logger = logging.getLogger(__name__)

    payload_template = userdata.get(topic)
    payload = copy.deepcopy(
        payload_template.payload
    )  # use deepcopy to avoid changing the configuration
    time_start = int(time.time() * 1000)
    payload["time"] = int(time_start)
    payload["timeEnd"] = int(time_start) + 500
    if not payload.get("tags"):
        payload["tags"] = []
    logger.debug(f"adding tags: {tags}")
    payload["tags"].extend(tags)
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
    configuration for MQTT and Grafana handling
    """

    def __init__(self, topic_config, grafana_url, headers):
        """
        :param topic_config: dictionary template for the payload to send to Grafana
        keyed by topic name
        :param grafana_url: Grafana base URL
        :param headers: HTTP headers
        """
        self.topic_config = topic_config
        self.grafana_url = grafana_url
        self.headers = headers


def main():
    """
    main CLI
    """
    args = handle_args()

    logging.basicConfig()
    logger = logging.getLogger(__package__)
    logger.setLevel(args.loglevel)
    logger.info("Running")

    logger.info(f"Reading HTTP headers from {args.headers}")
    with open(args.headers, encoding="utf-8") as file_handle:
        headers = json.load(file_handle)
        logger.debug(f"Got headers: {headers}")

    logger.info(f"Reading configuration from {args.config}")
    with open(args.config, encoding="utf-8") as file_handle:
        topic_config = json.load(file_handle)
        logger.debug(f"Got config: {topic_config}")

    # Check that each specific topic has a payload template in the configuration.
    # The contents of the template are not checked.
    logger.debug(f"Checking configuration for topics {args.topic}")
    for topic in args.topic:
        if topic not in topic_config.keys():
            raise FatalError(f"no configuration for topic '{topic}'")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    user_data = Userdata(topic_config, args.grafana_url, headers)
    client.user_data_set(user_data)
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        keep_alive = 60
        logger.info(
            f"Connecting to MQTT broker on {args.mqtt_hostname}:{args.mqtt_port}"
        )
        client.connect(args.mqtt_hostname, args.mqtt_port, keep_alive)
    except OSError as exc:
        raise FatalError("MQTT connect error") from exc

    for topic in args.topic:
        logger.info(f"Subscribing to topic {topic}")
        client.subscribe(topic)

    logging.info("entering MQTT loop")
    client.loop_forever()


def handle_args():
    """
    command line options handling
    :return: args structure
    """
    parser = argparse.ArgumentParser(
        description="convert MQTT messages to Grafana annotations",
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
        action="append",
        help="MQTT topic to subscribe to",
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.json",
        help="JSON file with Grafana payload configuration",
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
    return args


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except FatalError as fatal_exc:
        logging.getLogger(__name__).fatal(f"cannot continue: {fatal_exc}")
        sys.exit(1)
