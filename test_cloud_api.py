from uuid import UUID

from fastapi.testclient import TestClient

from cloud_api import create_app


class FakePublisher:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self.calls = []

    def publish_command(
        self,
        command_id,
        vehicle_id,
        action,
    ):
        if self.should_fail:
            raise ConnectionError(
                "MQTT broker unavailable"
            )

        self.calls.append(
            {
                "command_id": command_id,
                "vehicle_id": vehicle_id,
                "action": action,
            }
        )


def test_unlock_command_is_accepted_asynchronously():
    publisher = FakePublisher()
    app = create_app(publisher)
    client = TestClient(app)

    response = client.post(
        "/vehicles/JMC-001/commands/unlock"
    )

    assert response.status_code == 202

    command = response.json()
    UUID(command["command_id"])

    assert command["vehicle_id"] == "JMC-001"
    assert command["action"] == "unlock"
    assert command["status"] == "pending"
    assert command["door_locked"] is None

    assert publisher.calls == [
        {
            "command_id": command["command_id"],
            "vehicle_id": "JMC-001",
            "action": "unlock",
        }
    ]

    query_response = client.get(
        f"/commands/{command['command_id']}"
    )

    assert query_response.status_code == 200
    assert query_response.json()["status"] == "pending"


def test_unlock_unknown_vehicle_is_rejected():
    publisher = FakePublisher()
    client = TestClient(create_app(publisher))

    response = client.post(
        "/vehicles/UNKNOWN/commands/unlock"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "vehicle not found"
    }
    assert publisher.calls == []


def test_get_unknown_command_returns_404():
    publisher = FakePublisher()
    client = TestClient(create_app(publisher))

    response = client.get(
        "/commands/unknown-command"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "command not found"
    }


def test_mqtt_publish_failure_returns_503():
    publisher = FakePublisher(should_fail=True)
    app = create_app(publisher)
    client = TestClient(app)

    response = client.post(
        "/vehicles/JMC-001/commands/unlock"
    )

    assert response.status_code == 503

    detail = response.json()["detail"]
    command_id = detail["command_id"]

    assert detail["message"] == "MQTT publish failed"

    stored_command = app.state.command_store.get(
        command_id
    )

    assert stored_command["status"] == "failed"
    assert (
        stored_command["reason"]
        == "mqtt_publish_failed"
    )