import json
import threading

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion


BROKER_HOST = "127.0.0.1"
BROKER_PORT = 1883
STATUS_TOPIC = "vehicle/JMC-001/status"

connected_event = threading.Event()
connection_errors = []


def on_connect(
    client,
    userdata,
    flags,
    reason_code,
    properties,
):
    if reason_code.is_failure:
        connection_errors.append(str(reason_code))

    connected_event.set()


vehicle_status = {
    "vehicle_id": "JMC-001",
    "door_locked": True,
}

payload = json.dumps(
    vehicle_status,
    ensure_ascii=False,
)

client = mqtt.Client(
    CallbackAPIVersion.VERSION2,
    client_id="vehicle-status-publisher",
)

client.on_connect = on_connect
client.connect(BROKER_HOST, BROKER_PORT, keepalive=30)
client.loop_start()

try:
    if not connected_event.wait(timeout=5):
        raise TimeoutError("MQTT connection timed out")

    if connection_errors:
        raise ConnectionError(
            f"MQTT connection failed: {connection_errors[0]}"
        )

    message_info = client.publish(
        topic=STATUS_TOPIC,
        payload=payload,
        qos=1,
    )

    message_info.wait_for_publish(timeout=5)

    if not message_info.is_published():
        raise TimeoutError("MQTT publish acknowledgment timed out")

    print(f"Published topic: {STATUS_TOPIC}")
    print(f"Published payload: {payload}")
    print("Publish acknowledged by broker")
finally:
    client.disconnect()
    client.loop_stop()