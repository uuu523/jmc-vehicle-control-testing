import json

import paho.mqtt.client as mqtt


class MqttCommandPublisher:
    """Publish cloud commands through an already-connected MQTT client."""

    def __init__(self, client, publish_timeout=5):
        self.client = client
        self.publish_timeout = publish_timeout

    def publish_command(
        self,
        command_id,
        vehicle_id,
        action,
    ):
        topic = f"vehicle/{vehicle_id}/command"
        payload = json.dumps(
            {
                "command_id": command_id,
                "action": action,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )

        message_info = self.client.publish(
            topic=topic,
            payload=payload,
            qos=1,
        )

        if message_info.rc != mqtt.MQTT_ERR_SUCCESS:
            raise ConnectionError(
                "MQTT publish rejected: "
                f"rc={message_info.rc}"
            )

        message_info.wait_for_publish(
            timeout=self.publish_timeout
        )

        if not message_info.is_published():
            raise TimeoutError(
                "MQTT publish acknowledgment timed out"
            )

        return {
            "topic": topic,
            "payload": payload,
        }
