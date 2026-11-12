'''
from vehicle_control import validate_control_password


def test_valid_password():
    result = validate_control_password("123456")
    assert result is True


def test_password_too_short():
    result = validate_control_password("12345")
    assert result is False


def test_password_too_long():
    result = validate_control_password("1234567")
    assert result is False


def test_password_contains_letter():
    result = validate_control_password("12345q")
    assert result is False


def test_empty_password():
    result = validate_control_password("")
    assert result is False
    '''

import pytest

from vehicle_control import validate_control_password


@pytest.mark.parametrize(
    "password, expected",
    [
        ("123456", True),
        ("12345", False),
        ("1234567", False),
        ("12345q", False),
        ("", False),
        ("000001", True),
        ("12 456", False),
    ],
)

def test_validate_control_password(password, expected):
    actual = validate_control_password(password)
    assert actual is expected