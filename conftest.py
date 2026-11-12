import pytest


@pytest.fixture
def ready_vehicle():
    """准备一辆满足远程控制条件的测试车辆。"""
    return {
        "logged_in": True,
        "bound": True,
        "online": True,
        "door_locked": True,
        "correct_password": "123456",
        "failed_attempts": 0,
        "control_locked": False,
    }