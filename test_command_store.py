import pytest

from command_store import CommandStore


def build_success_result(command_id="cmd-001"):
    return {
        "command_id": command_id,
        "vehicle_id": "JMC-001",
        "action": "unlock",
        "status": "success",
        "reason": None,
        "door_locked": False,
        "duplicate": False,
    }


def test_create_command_has_pending_status():
    store = CommandStore()

    command = store.create(
        command_id="cmd-001",
        vehicle_id="JMC-001",
        action="unlock",
    )

    assert command["command_id"] == "cmd-001"
    assert command["status"] == "pending"
    assert command["door_locked"] is None
    assert command["completed_at"] is None


def test_apply_success_result_completes_command():
    store = CommandStore()
    store.create("cmd-001", "JMC-001", "unlock")

    completed = store.apply_result(
        build_success_result()
    )

    assert completed["status"] == "success"
    assert completed["reason"] is None
    assert completed["door_locked"] is False
    assert completed["completed_at"] is not None


def test_duplicate_result_does_not_overwrite_final_status():
    store = CommandStore()
    store.create("cmd-001", "JMC-001", "unlock")

    store.apply_result(build_success_result())

    duplicate_failure = build_success_result()
    duplicate_failure["status"] = "failed"
    duplicate_failure["reason"] = "late_duplicate"

    final_command = store.apply_result(
        duplicate_failure
    )

    assert final_command["status"] == "success"
    assert final_command["reason"] is None


def test_result_with_different_action_is_rejected():
    store = CommandStore()
    store.create("cmd-001", "JMC-001", "unlock")

    invalid_result = build_success_result()
    invalid_result["action"] = "lock"

    with pytest.raises(
        ValueError,
        match="result action mismatch",
    ):
        store.apply_result(invalid_result)


def test_unknown_command_result_is_rejected():
    store = CommandStore()

    with pytest.raises(
        KeyError,
        match="command not found",
    ):
        store.apply_result(
            build_success_result("unknown-command")
        )

def test_get_returns_copy_of_command():
    store = CommandStore()
    store.create("cmd-001", "JMC-001", "unlock")

    command = store.get("cmd-001")
    command["status"] = "changed-outside-store"

    stored_command = store.get("cmd-001")

    assert stored_command["status"] == "pending"


def test_get_unknown_command_is_rejected():
    store = CommandStore()

    with pytest.raises(
        KeyError,
        match="command not found",
    ):
        store.get("unknown-command")


def test_duplicate_command_id_is_rejected():
    store = CommandStore()
    store.create("cmd-001", "JMC-001", "unlock")

    with pytest.raises(
        ValueError,
        match="command already exists",
    ):
        store.create("cmd-001", "JMC-001", "unlock")


def test_result_with_different_vehicle_is_rejected():
    store = CommandStore()
    store.create("cmd-001", "JMC-001", "unlock")

    invalid_result = build_success_result()
    invalid_result["vehicle_id"] = "JMC-999"

    with pytest.raises(
        ValueError,
        match="result vehicle_id mismatch",
    ):
        store.apply_result(invalid_result)


def test_result_with_invalid_status_is_rejected():
    store = CommandStore()
    store.create("cmd-001", "JMC-001", "unlock")

    invalid_result = build_success_result()
    invalid_result["status"] = "processing"

    with pytest.raises(
        ValueError,
        match="invalid result status",
    ):
        store.apply_result(invalid_result)