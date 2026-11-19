import pytest

from command_store import CommandStore
from mqtt_result_consumer import MqttResultConsumer


def build_consumer_with_pending_command():
    store = CommandStore()
    store.create("cmd-001", "JMC-001", "unlock")
    return store, MqttResultConsumer(store)


def test_result_consumer_completes_pending_command():
    store, consumer = build_consumer_with_pending_command()

    completed = consumer.handle_payload(
        "{"
        '"command_id":"cmd-001",'
        '"vehicle_id":"JMC-001",'
        '"action":"unlock",'
        '"status":"success",'
        '"reason":null,'
        '"door_locked":false'
        "}"
    )

    assert completed["status"] == "success"
    assert completed["door_locked"] is False
    assert store.get("cmd-001")["status"] == "success"


def test_result_consumer_rejects_invalid_json():
    _, consumer = build_consumer_with_pending_command()

    with pytest.raises(
        ValueError,
        match="invalid MQTT result JSON",
    ):
        consumer.handle_payload("not-json")


def test_result_consumer_rejects_non_object_json():
    _, consumer = build_consumer_with_pending_command()

    with pytest.raises(
        ValueError,
        match="must be a JSON object",
    ):
        consumer.handle_payload("[]")


def test_result_consumer_rejects_unknown_command():
    store = CommandStore()
    consumer = MqttResultConsumer(store)

    with pytest.raises(
        KeyError,
        match="command not found",
    ):
        consumer.handle_payload(
            "{"
            '"command_id":"unknown",'
            '"vehicle_id":"JMC-001",'
            '"action":"unlock",'
            '"status":"success"'
            "}"
        )
