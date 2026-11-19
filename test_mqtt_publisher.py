import json

import pytest

from mqtt_publisher import MqttCommandPublisher


class FakeMessageInfo:
    def __init__(self, rc=0, published=True):
        self.rc = rc
        self.published = published
        self.wait_timeout = None

    def wait_for_publish(self, timeout):
        self.wait_timeout = timeout

    def is_published(self):
        return self.published


class FakeMqttClient:
    def __init__(self, message_info):
        self.message_info = message_info
        self.publish_calls = []

    def publish(self, topic, payload, qos):
        self.publish_calls.append(
            {
                "topic": topic,
                "payload": payload,
                "qos": qos,
            }
        )
        return self.message_info


def test_publish_command_uses_vehicle_topic_and_qos_one():
    message_info = FakeMessageInfo()
    client = FakeMqttClient(message_info)
    publisher = MqttCommandPublisher(
        client,
        publish_timeout=3,
    )

    result = publisher.publish_command(
        command_id="cmd-001",
        vehicle_id="JMC-001",
        action="unlock",
    )

    assert len(client.publish_calls) == 1
    publish_call = client.publish_calls[0]
    assert (
        publish_call["topic"]
        == "vehicle/JMC-001/command"
    )
    assert publish_call["qos"] == 1
    assert json.loads(publish_call["payload"]) == {
        "command_id": "cmd-001",
        "action": "unlock",
    }
    assert message_info.wait_timeout == 3
    assert result["topic"] == publish_call["topic"]
    assert result["payload"] == publish_call["payload"]


def test_publish_command_rejects_mqtt_client_error():
    message_info = FakeMessageInfo(rc=4)
    client = FakeMqttClient(message_info)
    publisher = MqttCommandPublisher(client)

    with pytest.raises(
        ConnectionError,
        match="MQTT publish rejected: rc=4",
    ):
        publisher.publish_command(
            command_id="cmd-001",
            vehicle_id="JMC-001",
            action="unlock",
        )

    assert message_info.wait_timeout is None


def test_publish_command_rejects_acknowledgment_timeout():
    message_info = FakeMessageInfo(
        rc=0,
        published=False,
    )
    client = FakeMqttClient(message_info)
    publisher = MqttCommandPublisher(client)

    with pytest.raises(
        TimeoutError,
        match="acknowledgment timed out",
    ):
        publisher.publish_command(
            command_id="cmd-001",
            vehicle_id="JMC-001",
            action="unlock",
        )

    assert message_info.wait_timeout == 5
