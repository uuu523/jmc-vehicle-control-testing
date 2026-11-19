from uuid import uuid4

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import status as http_status

from command_store import CommandStore


KNOWN_VEHICLES = {"JMC-001"}


def create_app(publisher, store=None):
    command_store = (
        store
        if store is not None
        else CommandStore()
    )

    app = FastAPI(
        title="Connected Vehicle Cloud API",
        version="2.0.0",
    )
    app.state.command_store = command_store

    @app.post(
        "/vehicles/{vehicle_id}/commands/unlock",
        status_code=http_status.HTTP_202_ACCEPTED,
    )
    def create_unlock_command(vehicle_id):
        if vehicle_id not in KNOWN_VEHICLES:
            raise HTTPException(
                status_code=404,
                detail="vehicle not found",
            )

        command_id = str(uuid4())

        command = command_store.create(
            command_id=command_id,
            vehicle_id=vehicle_id,
            action="unlock",
        )

        try:
            publisher.publish_command(
                command_id=command_id,
                vehicle_id=vehicle_id,
                action="unlock",
            )
        except Exception as error:
            command_store.apply_result(
                {
                    "command_id": command_id,
                    "vehicle_id": vehicle_id,
                    "action": "unlock",
                    "status": "failed",
                    "reason": "mqtt_publish_failed",
                    "door_locked": None,
                }
            )

            raise HTTPException(
                status_code=503,
                detail={
                    "message": "MQTT publish failed",
                    "command_id": command_id,
                },
            ) from error

        return command

    @app.get("/commands/{command_id}")
    def get_command(command_id):
        try:
            return command_store.get(command_id)
        except KeyError as error:
            raise HTTPException(
                status_code=404,
                detail="command not found",
            ) from error

    return app