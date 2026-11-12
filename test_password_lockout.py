from vehicle_control import remote_unlock


def test_not_locked_after_four_wrong_passwords(ready_vehicle):
    for _ in range(4):
        response = remote_unlock(ready_vehicle, "654321")

    assert response["message"] == "wrong password"
    assert ready_vehicle["failed_attempts"] == 4
    assert ready_vehicle["control_locked"] is False
    assert ready_vehicle["door_locked"] is True


def test_locked_on_fifth_wrong_password(ready_vehicle):
    for _ in range(4):
        remote_unlock(ready_vehicle, "654321")

    response = remote_unlock(ready_vehicle, "654321")

    assert response["success"] is False
    assert response["message"] == "control locked"
    assert ready_vehicle["failed_attempts"] == 5
    assert ready_vehicle["control_locked"] is True
    assert ready_vehicle["door_locked"] is True


def test_correct_password_cannot_unlock_after_lockout(ready_vehicle):
    for _ in range(5):
        remote_unlock(ready_vehicle, "654321")

    response = remote_unlock(ready_vehicle, "123456")

    assert response["success"] is False
    assert response["message"] == "control locked"
    assert ready_vehicle["door_locked"] is True