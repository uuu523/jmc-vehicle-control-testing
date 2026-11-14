import json

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion


BROKER_HOST = "127.0.0.1"
BROKER_PORT = 1883
VEHICLE_ID = "JMC-001"


class TBoxSimulator:
    def __init__(self, vehicle_id):
        self.vehicle_id = vehicle_id
        self.door_locked = True

        self.command_topic = (
            f"vehicle/{vehicle_id}/command"
        )
        self.result_topic = (
            f"vehicle/{vehicle_id}/result"
        )

        self.client = mqtt.Client(
            CallbackAPIVersion.VERSION2,
            client_id=f"tbox-{vehicle_id}",
        )

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    def on_connect(
        self,
        client,
        userdata,
        flags,
        reason_code,
        properties,
    ):
        if reason_code.is_failure:
            print(f"Connection failed: {reason_code}")
            return

        client.subscribe(
            self.command_topic,
            qos=1,
        )

        print(f"Connected to MQTT broker")
        print(f"Subscribed topic: {self.command_topic}")
        print(
            f"Initial door state: "
            f"door_locked={self.door_locked}"
        )

    def on_message(
        self,
        client,
        userdata,
        message,
    ):
        raw_payload = message.payload.decode("utf-8")

        print(f"\nReceived topic: {message.topic}")
        print(f"Received payload: {raw_payload}")

        try:
            command = json.loads(raw_payload)
        except json.JSONDecodeError:
            self.publish_result(
                command_id=None,
                action=None,
                status="failed",
                reason="invalid_json",
            )
            return

        command_id = command.get("command_id")
        action = command.get("action")

        if not isinstance(command_id, str) or not command_id:
            self.publish_result(
                command_id=command_id,
                action=action,
                status="failed",
                reason="invalid_command_id",
            )
            return

        if action == "unlock":
            self.door_locked = False

            self.publish_result(
                command_id=command_id,
                action=action,
                status="success",
                reason=None,
            )
            return

        self.publish_result(
            command_id=command_id,
            action=action,
            status="failed",
            reason="unsupported_action",
        )

    def publish_result(
        self,
        command_id,
        action,
        status,
        reason,
    ):
        result = {
            "command_id": command_id,
            "vehicle_id": self.vehicle_id,
            "action": action,
            "status": status,
            "reason": reason,
            "door_locked": self.door_locked,
        }

        payload = json.dumps(
            result,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        message_info = self.client.publish(
            topic=self.result_topic,
            payload=payload,
            qos=1,
        )

        if message_info.rc != mqtt.MQTT_ERR_SUCCESS:
            print(
                "Failed to queue result: "
                f"rc={message_info.rc}"
            )
            return

        print(f"Published topic: {self.result_topic}")
        print(f"Published result: {payload}")

    def on_disconnect(
        self,
        client,
        userdata,
        disconnect_flags,
        reason_code,
        properties,
    ):
        print(f"Disconnected: {reason_code}")

    def run(self):
        print(
            f"Connecting to MQTT broker "
            f"{BROKER_HOST}:{BROKER_PORT}"
        )

        self.client.connect(
            BROKER_HOST,
            BROKER_PORT,
            keepalive=30,
        )

        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("\nStopping T-BOX simulator")
        finally:
            self.client.disconnect()


if __name__ == "__main__":
    simulator = TBoxSimulator(VEHICLE_ID)
    simulator.run()