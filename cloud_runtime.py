import os
from contextlib import asynccontextmanager

from cloud_api import create_app
from cloud_mqtt import CloudMqttClient
from command_store import CommandStore


BROKER_HOST = os.getenv(
    "MQTT_BROKER_HOST",
    "127.0.0.1",
)
BROKER_PORT = int(
    os.getenv("MQTT_BROKER_PORT", "1883")
)

command_store = CommandStore()
cloud_mqtt = CloudMqttClient(
    command_store=command_store,
    broker_host=BROKER_HOST,
    broker_port=BROKER_PORT,
)


@asynccontextmanager
async def lifespan(app):
    cloud_mqtt.start()
    try:
        yield
    finally:
        cloud_mqtt.stop()


app = create_app(
    publisher=cloud_mqtt.publisher,
    store=command_store,
    lifespan=lifespan,
)
