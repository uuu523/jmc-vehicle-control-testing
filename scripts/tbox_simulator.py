import json
import os

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from tbox_logic import TBoxController


BROKER_HOST = os.getenv(
    "MQTT_BROKER_HOST",
    "127.0.0.1",
)
BROKER_PORT = int(
    os.getenv("MQTT_BROKER_PORT", "1883")
)
VEHICLE_ID = os.getenv(
    "VEHICLE_ID",
    "JMC-001",
)


class TBoxSimulator:
    def __init__(self, vehicle_id):
        self.vehicle_id = vehicle_id
        self.controller = TBoxController(vehicle_id)

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

        print("Connected to MQTT broker")
        print(f"Subscribed topic: {self.command_topic}")
        print(
            "Initial door state: "
            f"door_locked={self.controller.door_locked}"
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

        result = self.controller.handle_command(
            raw_payload
        )

        self.publish_result(result)

    def publish_result(self, result):
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
