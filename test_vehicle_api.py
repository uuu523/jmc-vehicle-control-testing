import logging
import pytest

from vehicle_control import remote_unlock
from fastapi.testclient import TestClient

from vehicle_api import app, vehicle_store


@pytest.fixture
def api_client(ready_vehicle):
    """每条接口用例开始前，重新准备车辆数据。"""
    vehicle_store.clear()
    vehicle_store["JMC-001"] = ready_vehicle

    return TestClient(app)


def test_unlock_api_success(api_client):
    """正确密码能够成功解锁。"""
    response = api_client.post(
        "/vehicles/JMC-001/unlock",
        json={"password": "123456"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "unlock success",
    }
    assert vehicle_store["JMC-001"]["door_locked"] is False


def test_unlock_api_when_vehicle_offline(api_client, caplog):
    vehicle_store["JMC-001"]["online"] = False

    with caplog.at_level(logging.INFO, logger="vehicle_api"):
        response = api_client.post(
            "/vehicles/JMC-001/unlock",
            json={"password": "123456"},
        )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "vehicle offline",
    }
    assert vehicle_store["JMC-001"]["door_locked"] is True

    assert "unlock_request vehicle_id=JMC-001" in caplog.text
    assert "status=409" in caplog.text
    assert "reason=vehicle_offline" in caplog.text


def test_unlock_api_when_vehicle_not_found(api_client):
    """车辆编号不存在时返回404。"""
    response = api_client.post(
        "/vehicles/UNKNOWN/unlock",
        json={"password": "123456"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "vehicle not found",
    }


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(
            {"password": "12345"},
            id="password-too-short",
        ),
        pytest.param(
            {"password": "1234567"},
            id="password-too-long",
        ),
        pytest.param(
            {"password": "12345q"},
            id="password-contains-letter",
        ),
        pytest.param(
            {"password": ""},
            id="password-empty",
        ),
        pytest.param(
            {},
            id="password-missing",
        ),
    ],
)
def test_unlock_api_rejects_invalid_password_format(api_client, payload):
    """密码格式不符合要求时返回422。"""
    response = api_client.post(
        "/vehicles/JMC-001/unlock",
        json=payload,
    )

    assert response.status_code == 422
    assert vehicle_store["JMC-001"]["door_locked"] is True


def test_unlock_api_rejects_wrong_password(api_client):
    """密码格式正确但内容错误时返回400。"""
    response = api_client.post(
        "/vehicles/JMC-001/unlock",
        json={"password": "654321"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "wrong password",
    }
    assert vehicle_store["JMC-001"]["failed_attempts"] == 1
    assert vehicle_store["JMC-001"]["door_locked"] is True

def test_request_id_is_propagated(api_client, caplog):
    request_id = "test-trace-001"

    with caplog.at_level(logging.INFO, logger="vehicle_api"):
        response = api_client.post(
            "/vehicles/JMC-001/unlock",
            headers={"X-Request-ID": request_id},
            json={"password": "123456"},
        )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id
    assert f"request_id={request_id}" in caplog.text


def test_request_id_is_generated_when_missing(api_client):
    response = api_client.post(
        "/vehicles/JMC-001/unlock",
        json={"password": "123456"},
    )

    generated_request_id = response.headers.get("X-Request-ID")

    assert response.status_code == 200
    assert generated_request_id is not None
    assert len(generated_request_id) == 36

def test_unlock_api_when_vehicle_timeout(
    api_client,
    monkeypatch,
    caplog,
):
    def raise_timeout(vehicle, password):
        raise TimeoutError("simulated T-BOX timeout")

    monkeypatch.setattr(
        "vehicle_api.send_unlock_command",
        raise_timeout,
    )

    request_id = "test-timeout-001"

    with caplog.at_level(logging.INFO, logger="vehicle_api"):
        response = api_client.post(
            "/vehicles/JMC-001/unlock",
            headers={"X-Request-ID": request_id},
            json={"password": "123456"},
        )

    assert response.status_code == 504
    assert response.json() == {
        "detail": "vehicle response timeout"
    }
    assert response.headers["X-Request-ID"] == request_id

    # 本次模拟的是“指令执行前发生超时”，所以状态不应改变
    assert vehicle_store["JMC-001"]["door_locked"] is True

    assert "request_id=test-timeout-001" in caplog.text
    assert "status=504" in caplog.text
    assert "reason=vehicle_timeout" in caplog.text

def test_vehicle_may_unlock_before_response_timeout(
    api_client,
    monkeypatch,
):
    def unlock_then_timeout(vehicle, password):
        # 车辆已经执行了解锁
        remote_unlock(vehicle, password)

        # 但是响应在返回途中丢失
        raise TimeoutError("response lost after vehicle unlocked")

    monkeypatch.setattr(
        "vehicle_api.send_unlock_command",
        unlock_then_timeout,
    )

    response = api_client.post(
        "/vehicles/JMC-001/unlock",
        headers={"X-Request-ID": "test-response-lost-001"},
        json={"password": "123456"},
    )

    # 云端没有收到车端响应，所以接口仍返回超时
    assert response.status_code == 504

    # 但车辆实际上已经解锁
    assert vehicle_store["JMC-001"]["door_locked"] is False

def test_query_vehicle_status_after_unlock_response_lost(
    api_client,
    monkeypatch,
):
    def unlock_then_timeout(vehicle, password):
        remote_unlock(vehicle, password)
        raise TimeoutError("response lost after vehicle unlocked")

    monkeypatch.setattr(
        "vehicle_api.send_unlock_command",
        unlock_then_timeout,
    )

    unlock_response = api_client.post(
        "/vehicles/JMC-001/unlock",
        headers={"X-Request-ID": "unlock-001"},
        json={"password": "123456"},
    )

    # 云端只知道响应超时
    assert unlock_response.status_code == 504

    status_response = api_client.get(
        "/vehicles/JMC-001/status",
        headers={"X-Request-ID": "status-query-001"},
    )

    assert status_response.status_code == 200
    assert status_response.json() == {
        "vehicle_id": "JMC-001",
        "online": True,
        "door_locked": False,
    }