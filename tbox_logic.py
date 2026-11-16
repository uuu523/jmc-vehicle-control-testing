import json


class TBoxController:
    def __init__(self, vehicle_id):
        self.vehicle_id = vehicle_id
        self.door_locked = True

    def handle_command(self, raw_payload):
        try:
            command = json.loads(raw_payload)
        except json.JSONDecodeError:
            return self._build_result(
                command_id=None,
                action=None,
                status="failed",
                reason="invalid_json",
            )

        command_id = command.get("command_id")
        action = command.get("action")

        if not isinstance(command_id, str) or not command_id:
            return self._build_result(
                command_id=command_id,
                action=action,
                status="failed",
                reason="invalid_command_id",
            )

        if action == "unlock":
            self.door_locked = False

            return self._build_result(
                command_id=command_id,
                action=action,
                status="success",
                reason=None,
            )

        return self._build_result(
            command_id=command_id,
            action=action,
            status="failed",
            reason="unsupported_action",
        )

    def _build_result(
        self,
        command_id,
        action,
        status,
        reason,
    ):
        return {
            "command_id": command_id,
            "vehicle_id": self.vehicle_id,
            "action": action,
            "status": status,
            "reason": reason,
            "door_locked": self.door_locked,
        }