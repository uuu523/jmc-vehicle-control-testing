import pytest

from tbox_logic import TBoxController


def test_tbox_executes_unlock_command():
    controller = TBoxController("JMC-001")

    result = controller.handle_command(
        '{"command_id":"cmd-001","action":"unlock"}'
    )

    assert result == {
        "command_id": "cmd-001",
        "vehicle_id": "JMC-001",
        "action": "unlock",
        "status": "success",
        "reason": None,
        "door_locked": False,
        "duplicate": False,
    }


@pytest.mark.parametrize(
    ("raw_payload", "expected_reason"),
    [
        ("not-json", "invalid_json"),
        ('{"action":"unlock"}', "invalid_command_id"),
        (
            '{"command_id":"cmd-002","action":"start_engine"}',
            "unsupported_action",
        ),
    ],
    ids=[
        "invalid-json",
        "missing-command-id",
        "unsupported-action",
    ],
)
def test_tbox_rejects_invalid_command(
    raw_payload,
    expected_reason,
):
    controller = TBoxController("JMC-001")

    result = controller.handle_command(raw_payload)

    assert result["status"] == "failed"
    assert result["reason"] == expected_reason
    assert result["door_locked"] is True
    assert result["duplicate"] is False


def test_duplicate_unlock_command_is_not_executed_again():
    controller = TBoxController("JMC-001")
    command = '{"command_id":"cmd-003","action":"unlock"}'

    first_result = controller.handle_command(command)
    second_result = controller.handle_command(command)

    assert first_result["status"] == "success"
    assert first_result["duplicate"] is False

    assert second_result["status"] == "success"
    assert second_result["duplicate"] is True
    assert second_result["door_locked"] is False

    assert len(controller.processed_commands) == 1


def test_same_command_id_with_different_action_is_rejected():
    controller = TBoxController("JMC-001")

    controller.handle_command(
        '{"command_id":"cmd-004","action":"unlock"}'
    )

    conflict_result = controller.handle_command(
        '{"command_id":"cmd-004","action":"lock"}'
    )

    assert conflict_result["status"] == "failed"
    assert conflict_result["reason"] == "command_id_conflict"
    assert conflict_result["duplicate"] is True
    assert conflict_result["door_locked"] is False