def validate_control_password(password):
    """检查车辆控制密码是否为6位纯数字。"""
    return len(password) == 6 and password.isdigit()
def remote_unlock(vehicle, password):
    """模拟远程解锁车辆。"""

    if not vehicle["logged_in"]:
        return {"success": False, "message": "user not logged in"}

    if not vehicle["bound"]:
        return {"success": False, "message": "vehicle not bound"}

    if not vehicle["online"]:
        return {"success": False, "message": "vehicle offline"}

    if vehicle["control_locked"]:
        return {"success": False, "message": "control locked"}

    if password != vehicle["correct_password"]:
        vehicle["failed_attempts"] += 1

        if vehicle["failed_attempts"] >= 5:
            vehicle["control_locked"] = True
            return {"success": False, "message": "control locked"}

        return {"success": False, "message": "wrong password"}

    vehicle["failed_attempts"] = 0
    vehicle["door_locked"] = False
    return {"success": True, "message": "unlock success"}