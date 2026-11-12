'''
import pytest
'''
from vehicle_control import remote_unlock

def test_unlock_success(ready_vehicle):
    response = remote_unlock(ready_vehicle, "123456")

    assert response["success"] is True
    assert response["message"] == "unlock success"
    assert ready_vehicle["door_locked"] is False


def test_unlock_when_vehicle_offline(ready_vehicle):
    ready_vehicle["online"] = False

    response = remote_unlock(ready_vehicle, "123456")

    assert response["success"] is False
    assert response["message"] == "vehicle offline"
    assert ready_vehicle["door_locked"] is True


def test_unlock_when_user_not_logged_in(ready_vehicle):
    ready_vehicle["logged_in"] = False

    response = remote_unlock(ready_vehicle, "123456")

    assert response["success"] is False
    assert response["message"] == "user not logged in"
    assert ready_vehicle["door_locked"] is True

def test_unlock_when_vehicle_not_bound(ready_vehicle):
    ready_vehicle["bound"] = False

    result = remote_unlock(
        ready_vehicle,
        "123456",
    )

    assert result == {
        "success": False,
        "message": "vehicle not bound",
    }
    assert ready_vehicle["door_locked"] is True