import json


class TBoxController:
    def __init__(self, vehicle_id):
        self.vehicle_id = vehicle_id
        self.door_locked = True

        # 保存已经成功处理过的指令
        # command_id -> {"action": ..., "result": ...}
        self.processed_commands = {}

    def handle_command(self, raw_payload):
        try:
            command = json.loads(raw_payload)
        except json.JSONDecodeError:
            return self._build_result(
                command_id=None,
                action=None,
                status="failed",
                reason="invalid_json",
                duplicate=False,
            )

        command_id = command.get("command_id")
        action = command.get("action")

        if not isinstance(command_id, str) or not command_id:
            return self._build_result(
                command_id=command_id,
                action=action,
                status="failed",
                reason="invalid_command_id",
                duplicate=False,
            )

        # 检查 command_id 是否处理过
        if command_id in self.processed_commands:
            saved_command = self.processed_commands[command_id]

            # 相同 command_id 却对应不同操作，属于冲突
            if action != saved_command["action"]:
                return self._build_result(
                    command_id=command_id,
                    action=action,
                    status="failed",
                    reason="command_id_conflict",
                    duplicate=True,
                )

            # 相同指令重复到达，不再执行，直接返回第一次的结果
            cached_result = saved_command["result"].copy()
            cached_result["duplicate"] = True
            return cached_result

        if action == "unlock":
            self.door_locked = False

            result = self._build_result(
                command_id=command_id,
                action=action,
                status="success",
                reason=None,
                duplicate=False,
            )

            self.processed_commands[command_id] = {
                "action": action,
                "result": result.copy(),
            }

            return result

        return self._build_result(
            command_id=command_id,
            action=action,
            status="failed",
            reason="unsupported_action",
            duplicate=False,
        )

    def _build_result(
        self,
        command_id,
        action,
        status,
        reason,
        duplicate,
    ):
        return {
            "command_id": command_id,
            "vehicle_id": self.vehicle_id,
            "action": action,
            "status": status,
            "reason": reason,
            "door_locked": self.door_locked,
            "duplicate": duplicate,
        }