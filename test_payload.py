"""
MQTT payload handling tests
"""

import json
import unittest
from unittest.mock import MagicMock, Mock, patch

from mq2anno import Userdata, on_message


class TestPayloadHandling(unittest.TestCase):
    """payload handling tests"""

    @patch("mq2anno.requests")
    def test_payload_positive(self, mock_requests):
        """
        Verify that payload handling in on_message() works correctly for the positive case.
        """
        payload = json.dumps({"annotation": True, "tags": ["foo", "bar"]})
        msg = Mock()
        msg.payload = payload
        msg.topic = "foo"
        topic_cfg = {msg.topic: {"aaa": "bbb"}}
        url = "http://localhost:8080"
        userdata = Userdata(topic_cfg, url, {})

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "userId": 1,
            "id": 1,
            "title": "hello",
        }
        mock_requests.post.return_value = mock_response

        on_message(None, userdata, msg)

        mock_requests.post.assert_called_once()
        assert len(mock_requests.post.call_args) >= 1
        assert mock_requests.post.call_args[0][0] == url + "/api/annotations"

    @patch("mq2anno.requests")
    def test_payload_negative(self, mock_requests):
        """
        Verify that payload handling in on_message() works correctly for the negative cases.
        """
        payloads = [
            {"annotation": True},
            {"annotation": False},
            {"annotation": False, "tags": ["foo"]},
            {"annotation": True, "tags": "bar"},
        ]
        for payload_dict in payloads:
            payload = json.dumps(payload_dict)
            with self.subTest(payload):
                msg = Mock()
                msg.payload = payload
                msg.topic = "foo"
                topic_cfg = {msg.topic: {"aaa": "bbb"}}
                url = "http://localhost:8080"
                userdata = Userdata(topic_cfg, url, {})

                on_message(None, userdata, msg)

                mock_requests.post.assert_not_called()
