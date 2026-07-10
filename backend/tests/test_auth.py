from app.core.config import settings
from tests.conftest import register_and_login

API = "/api/v1/auth"


def test_registration_can_be_disabled(client, monkeypatch):
    # สมัคร user แรกไว้ก่อนปิด (จำลอง flow ใช้จริง)
    headers = register_and_login(client)

    monkeypatch.setattr(settings, "REGISTRATION_ENABLED", False)
    res = client.post(
        API + "/register",
        json={"email": "new@example.com", "password": "password123"},
    )
    assert res.status_code == 403

    # user เดิมยัง login / ใช้งานได้ปกติ
    login = client.post(
        API + "/login",
        json={"email": "deen@example.com", "password": "password123"},
    )
    assert login.status_code == 200
    assert client.get(API + "/me", headers=headers).status_code == 200


def test_registration_enabled_by_default(client):
    res = client.post(
        API + "/register",
        json={"email": "a@example.com", "password": "password123"},
    )
    assert res.status_code == 201
