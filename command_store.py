from datetime import datetime, timezone
from threading import Lock


TERMINAL_STATUSES = {"success", "failed"}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class CommandStore:
    def __init__(self):
        self._commands = {}
        self._lock = Lock()

    def create(self, command_id, vehicle_id, action):
        with self._lock:
            if command_id in self._commands:
                raise ValueError(
                    f"command already exists: {command_id}"
                )

            command = {
                "command_id": command_id,
                "vehicle_id": vehicle_id,
                "action": action,
                "status": "pending",
                "reason": None,
                "door_locked": None,
                "created_at": utc_now(),
                "completed_at": None,
            }

            self._commands[command_id] = command
            return command.copy()

    def get(self, command_id):
        with self._lock:
            if command_id not in self._commands:
                raise KeyError(
                    f"command not found: {command_id}"
                )

            return self._commands[command_id].copy()

    def apply_result(self, result):
        command_id = result.get("command_id")

        with self._lock:
            if command_id not in self._commands:
                raise KeyError(
                    f"command not found: {command_id}"
                )

            command = self._commands[command_id]

            if result.get("vehicle_id") != command["vehicle_id"]:
                raise ValueError("result vehicle_id mismatch")

            if result.get("action") != command["action"]:
                raise ValueError("result action mismatch")

            result_status = result.get("status")
            if result_status not in TERMINAL_STATUSES:
                raise ValueError(
                    f"invalid result status: {result_status}"
                )

            # 指令已经结束时，不允许后续重复消息改写最终结果
            if command["status"] in TERMINAL_STATUSES:
                return command.copy()

            command["status"] = result_status
            command["reason"] = result.get("reason")
            command["door_locked"] = result.get("door_locked")
            command["completed_at"] = utc_now()

            return command.copy()