import logging
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from vehicle_control import remote_unlock


logger = logging.getLogger("vehicle_api")

app = FastAPI(title="JMC Vehicle Control API")


class UnlockRequest(BaseModel):
    password: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^[0-9]{6}$",
    )


vehicle_store = {}
def send_unlock_command(vehicle, password):
    """模拟云端向T-BOX发送解锁指令。"""
    return remote_unlock(vehicle, password)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid4())

    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


@app.post("/vehicles/{vehicle_id}/unlock")
def unlock_vehicle(
    vehicle_id: str,
    payload: UnlockRequest,
    request: Request,
):
    request_id = request.state.request_id

    logger.info(
        "request_id=%s event=unlock_request vehicle_id=%s",
        request_id,
        vehicle_id,
    )

    vehicle = vehicle_store.get(vehicle_id)

    if vehicle is None:
        logger.warning(
            "request_id=%s event=unlock_response "
            "vehicle_id=%s status=404 reason=vehicle_not_found",
            request_id,
            vehicle_id,
        )

        raise HTTPException(
            status_code=404,
            detail="vehicle not found",
        )

    try:
        result = send_unlock_command(vehicle, payload.password)
    except TimeoutError:
        logger.error(
            "request_id=%s event=unlock_response "
            "vehicle_id=%s status=504 reason=vehicle_timeout",
            request_id,
            vehicle_id,
        )
        raise HTTPException(
            status_code=504,
            detail="vehicle response timeout",
        )

    if result["success"]:
        logger.info(
            "request_id=%s event=unlock_response "
            "vehicle_id=%s status=200 reason=unlock_success",
            request_id,
            vehicle_id,
        )

        return result

    if result["message"] == "vehicle offline":
        logger.warning(
            "request_id=%s event=unlock_response "
            "vehicle_id=%s status=409 reason=vehicle_offline",
            request_id,
            vehicle_id,
        )

        raise HTTPException(
            status_code=409,
            detail="vehicle offline",
        )

    logger.warning(
        "request_id=%s event=unlock_response "
        "vehicle_id=%s status=400 reason=%s",
        request_id,
        vehicle_id,
        result["message"].replace(" ", "_"),
    )

    raise HTTPException(
        status_code=400,
        detail=result["message"],
    )

@app.get("/vehicles/{vehicle_id}/status")
def get_vehicle_status(
    vehicle_id: str,
    request: Request,
):
    request_id = request.state.request_id

    logger.info(
        "request_id=%s event=status_request vehicle_id=%s",
        request_id,
        vehicle_id,
    )

    vehicle = vehicle_store.get(vehicle_id)

    if vehicle is None:
        logger.warning(
            "request_id=%s event=status_response "
            "vehicle_id=%s status=404 reason=vehicle_not_found",
            request_id,
            vehicle_id,
        )
        raise HTTPException(
            status_code=404,
            detail="vehicle not found",
        )

    logger.info(
        "request_id=%s event=status_response "
        "vehicle_id=%s status=200 door_locked=%s",
        request_id,
        vehicle_id,
        vehicle["door_locked"],
    )

    return {
        "vehicle_id": vehicle_id,
        "online": vehicle["online"],
        "door_locked": vehicle["door_locked"],
    }