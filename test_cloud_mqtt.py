import logging

import pytest

from cloud_mqtt import CloudMqttClient
from command_store import CommandStore


class FakeReasonCode:
    def __init__(self, is_failure=False):
        self.is_failure = is_failure

    def __str__(self):
        return "connection refused"


class FakeMqttClient:
    def __init__(
        self,
        connect_callback=True,
        connection_failure=False,
        subscribe_result=0,
    ):
        self.connect_callback = connect_callback
        self.connection_failure = connection_failure
        self.subscribe_result = subscribe_result
        self.on_connect = None
        self.on_message = None
        self.connect_calls = []
        self.subscribe_calls = []
        self.loop_started = False
        self.loop_stopped = False
        self.disconnected = False

    def connect(self, host, port, keepalive):
        self.connect_calls.append(
            (host, port, keepalive)
        )
        if self.connect_callback:
            self.on_connect(
                self,
                None,
                None,
                FakeReasonCode(
                    self.connection_failure
                ),
                None,
            )

    def subscribe(self, topic, qos):
        self.subscribe_calls.append((topic, qos))
        return self.subscribe_result, 1

    def loop_start(self):
        self.loop_started = True

    def disconnect(self):
        self.disconnected = True

    def loop_stop(self):
        self.loop_stopped = True


class FakeMessage:
    def __init__(self, payload, topic="vehicle/JMC-001/result"):
        self.payload = payload
        self.topic = topic


def test_cloud_mqtt_connects_and_subscribes_to_results():
    client = FakeMqttClient()
    runtime = CloudMqttClient(
        CommandStore(),
        broker_host="mqtt.example",
        broker_port=2883,
        client=client,
    )

    runtime.start()

    assert client.connect_calls == [
        ("mqtt.example", 2883, 30)
    ]
    assert client.loop_started is True
    assert client.subscribe_calls == [
        ("vehicle/+/result", 1)
    ]

    runtime.stop()
    assert client.disconnected is True
    assert client.loop_stopped is True


def test_cloud_mqtt_rejects_connection_failure():
    client = FakeMqttClient(connection_failure=True)
    runtime = CloudMqttClient(
        CommandStore(),
        client=client,
    )

    with pytest.raises(
        ConnectionError,
        match="MQTT connection failed",
    ):
        runtime.start()

    assert client.disconnected is True


def test_cloud_mqtt_rejects_subscription_failure():
    client = FakeMqttClient(subscribe_result=4)
    runtime = CloudMqttClient(
        CommandStore(),
        client=client,
    )

    with pytest.raises(
        ConnectionError,
        match="result subscription failed",
    ):
        runtime.start()


def test_cloud_mqtt_rejects_connection_timeout():
    client = FakeMqttClient(connect_callback=False)
    runtime = CloudMqttClient(
        CommandStore(),
        connect_timeout=0,
        client=client,
    )

    with pytest.raises(
        TimeoutError,
        match="MQTT connection timed out",
    ):
        runtime.start()


def test_cloud_mqtt_applies_vehicle_result():
    store = CommandStore()
    store.create("cmd-001", "JMC-001", "unlock")
    client = FakeMqttClient()
    runtime = CloudMqttClient(store, client=client)
    message = FakeMessage(
        b'{"command_id":"cmd-001",'
        b'"vehicle_id":"JMC-001",'
        b'"action":"unlock",'
        b'"status":"success",'
        b'"reason":null,'
        b'"door_locked":false}'
    )

    client.on_message(client, None, message)

    assert store.get("cmd-001")["status"] == "success"


def test_cloud_mqtt_ignores_invalid_result(caplog):
    client = FakeMqttClient()
    runtime = CloudMqttClient(
        CommandStore(),
        client=client,
    )
    message = FakeMessage(b"not-json")

    with caplog.at_level(
        logging.WARNING,
        logger="cloud_mqtt",
    ):
        client.on_message(client, None, message)

    assert "ignored_mqtt_result" in caplog.text
