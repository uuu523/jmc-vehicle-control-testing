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
    }


@pytest.mark.parametrize(
    ("raw_payload", "expected_reason"),
    [
        (
            "not-json",
            "invalid_json",
        ),
        (
            '{"action":"unlock"}',
            "invalid_command_id",
        ),
        (
            (
                '{"command_id":"cmd-002",'
                '"action":"start_engine"}'
            ),
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