import json


class MqttResultConsumer:
    """Validate a T-BOX result and apply it to the command store."""

    def __init__(self, command_store):
        self.command_store = command_store

    def handle_payload(self, raw_payload):
        try:
            result = json.loads(raw_payload)
        except (json.JSONDecodeError, TypeError) as error:
            raise ValueError(
                "invalid MQTT result JSON"
            ) from error

        if not isinstance(result, dict):
            raise ValueError(
                "MQTT result must be a JSON object"
            )

        return self.command_store.apply_result(result)
