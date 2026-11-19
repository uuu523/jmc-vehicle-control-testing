import logging
import threading

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from mqtt_publisher import MqttCommandPublisher
from mqtt_result_consumer import MqttResultConsumer


LOGGER = logging.getLogger("cloud_mqtt")


class CloudMqttClient:
    """Own the cloud MQTT connection, publisher and result subscription."""

    RESULT_TOPIC = "vehicle/+/result"

    def __init__(
        self,
        command_store,
        broker_host="127.0.0.1",
        broker_port=1883,
        connect_timeout=5,
        client=None,
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.connect_timeout = connect_timeout
        self._connected_event = threading.Event()
        self._connection_error = None

        self.client = client or mqtt.Client(
            CallbackAPIVersion.VERSION2,
            client_id="vehicle-cloud-api",
        )
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        self.publisher = MqttCommandPublisher(
            self.client
        )
        self.result_consumer = MqttResultConsumer(
            command_store
        )

    def _on_connect(
        self,
        client,
        userdata,
        flags,
        reason_code,
        properties,
    ):
        if reason_code.is_failure:
            self._connection_error = ConnectionError(
                f"MQTT connection failed: {reason_code}"
            )
            self._connected_event.set()
            return

        subscribe_result, _ = client.subscribe(
            self.RESULT_TOPIC,
            qos=1,
        )

        if subscribe_result != mqtt.MQTT_ERR_SUCCESS:
            self._connection_error = ConnectionError(
                "MQTT result subscription failed: "
                f"rc={subscribe_result}"
            )

        self._connected_event.set()

    def _on_message(
        self,
        client,
        userdata,
        message,
    ):
        try:
            raw_payload = message.payload.decode("utf-8")
            completed = self.result_consumer.handle_payload(
                raw_payload
            )
            LOGGER.info(
                "command_result command_id=%s status=%s",
                completed["command_id"],
                completed["status"],
            )
        except (
            UnicodeDecodeError,
            ValueError,
            KeyError,
        ) as error:
            LOGGER.warning(
                "ignored_mqtt_result topic=%s error=%s",
                message.topic,
                error,
            )

    def start(self):
        self._connected_event.clear()
        self._connection_error = None

        self.client.connect(
            self.broker_host,
            self.broker_port,
            keepalive=30,
        )
        self.client.loop_start()

        if not self._connected_event.wait(
            timeout=self.connect_timeout
        ):
            self.stop()
            raise TimeoutError(
                "MQTT connection timed out"
            )

        if self._connection_error is not None:
            error = self._connection_error
            self.stop()
            raise error

    def stop(self):
        self.client.disconnect()
        self.client.loop_stop()
