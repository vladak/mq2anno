"""
MQTT payload handling tests
"""
import json

import unittest
from unittest.mock import MagicMock, Mock, patch
from mq2anno import on_message, Userdata


class TestPayloadHandling(unittest.TestCase):
    """payload handling tests"""

    # pylint: disable=no-self-use
    @patch("mq2anno.requests")
    def test_payload_processing(self, mock_requests):
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
