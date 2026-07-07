from datetime import timedelta

from app.modules.routines import service
from tests.conftest import register_and_login

API = "/api/v1/routines"


def iso(days_ago: int) -> str:
    # ใช้ตัวเดียวกับ server (UTC) — date.today() เป็นเวลาท้องถิ่น จะเพี้ยนช่วงหลังเที่ยงคืน
    return (service.today() - timedelta(days=days_ago)).isoformat()


def create_routine(client, headers, **overrides):
    payload = {"name": "ทดสอบ", "type": "daily", **overrides}
    res = client.post(API, json=payload, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()


# ---------- create + validation ----------


def test_create_daily(client, auth_headers):
    r = create_routine(client, auth_headers, name="วิ่ง", type="daily")
    assert r["type"] == "daily"
    assert r["freq_days"] is None and r["threshold"] is None
    assert r["done_today"] is False
    assert r["due"] is True  # daily ที่ยังไม่ทำวันนี้ = ถึงรอบ
    assert r["streak"] == 0
    assert r["last_7_days"] == [False] * 7


def test_create_interval_requires_freq_days(client, auth_headers):
    res = client.post(
        API, json={"name": "ตัดผม", "type": "interval"}, headers=auth_headers
    )
    assert res.status_code == 422


def test_create_as_needed_requires_threshold(client, auth_headers):
    res = client.post(
        API, json={"name": "ซักผ้า", "type": "as_needed"}, headers=auth_headers
    )
    assert res.status_code == 422


def test_create_daily_clears_irrelevant_fields(client, auth_headers):
    r = create_routine(client, auth_headers, type="daily", freq_days=7, threshold=3)
    assert r["freq_days"] is None and r["threshold"] is None


def test_list_filter_by_type(client, auth_headers):
    create_routine(client, auth_headers, name="วิ่ง", type="daily")
    create_routine(client, auth_headers, name="ตัดผม", type="interval", freq_days=30)
    res = client.get(API, params={"type": "interval"}, headers=auth_headers)
    assert res.status_code == 200
    assert [r["name"] for r in res.json()] == ["ตัดผม"]


# ---------- daily: checkin + streak ----------


def test_daily_checkin_and_cancel(client, auth_headers):
    r = create_routine(client, auth_headers, type="daily")
    rid = r["id"]

    res = client.post(f"{API}/{rid}/checkin", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["done_today"] is True
    assert body["due"] is False
    assert body["streak"] == 1
    assert body["last_7_days"][-1] is True
    assert body["last_done"] == iso(0)

    # กดซ้ำ = conflict (frontend ใช้ DELETE เพื่อยกเลิก)
    assert client.post(f"{API}/{rid}/checkin", headers=auth_headers).status_code == 409

    res = client.delete(f"{API}/{rid}/checkin", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["done_today"] is False
    assert body["streak"] == 0
    assert body["last_done"] is None


def test_daily_streak_counts_consecutive_days(client, auth_headers):
    rid = create_routine(client, auth_headers, type="daily")["id"]
    for days_ago in (2, 1, 0):
        res = client.post(
            f"{API}/{rid}/checkin", json={"date": iso(days_ago)}, headers=auth_headers
        )
        assert res.status_code == 200
    r = client.get(f"{API}/{rid}", headers=auth_headers).json()
    assert r["streak"] == 3
    assert r["last_7_days"] == [False, False, False, False, True, True, True]


def test_daily_streak_survives_pending_today(client, auth_headers):
    """เมื่อวานทำ วันนี้ยังไม่ทำ — streak ยังไม่ขาด"""
    rid = create_routine(client, auth_headers, type="daily")["id"]
    client.post(f"{API}/{rid}/checkin", json={"date": iso(1)}, headers=auth_headers)
    r = client.get(f"{API}/{rid}", headers=auth_headers).json()
    assert r["streak"] == 1
    assert r["done_today"] is False and r["due"] is True


def test_daily_streak_broken_by_gap(client, auth_headers):
    rid = create_routine(client, auth_headers, type="daily")["id"]
    client.post(f"{API}/{rid}/checkin", json={"date": iso(3)}, headers=auth_headers)
    r = client.get(f"{API}/{rid}", headers=auth_headers).json()
    assert r["streak"] == 0


def test_cancel_today_restores_previous_streak(client, auth_headers):
    rid = create_routine(client, auth_headers, type="daily")["id"]
    for days_ago in (1, 0):
        client.post(
            f"{API}/{rid}/checkin", json={"date": iso(days_ago)}, headers=auth_headers
        )
    r = client.delete(f"{API}/{rid}/checkin", headers=auth_headers).json()
    assert r["streak"] == 1  # streak คืนเป็นของเมื่อวาน


def test_checkin_future_date_rejected(client, auth_headers):
    rid = create_routine(client, auth_headers, type="daily")["id"]
    res = client.post(
        f"{API}/{rid}/checkin", json={"date": iso(-1)}, headers=auth_headers
    )
    assert res.status_code == 422


# ---------- interval ----------


def test_interval_without_last_done_is_due(client, auth_headers):
    r = create_routine(client, auth_headers, type="interval", freq_days=7)
    assert r["due"] is True
    assert r["days_until_due"] is None
    assert r["last_done"] is None


def test_interval_seeded_with_last_done(client, auth_headers):
    r = create_routine(
        client, auth_headers, type="interval", freq_days=7, last_done=iso(1)
    )
    assert r["last_done"] == iso(1)
    assert r["days_until_due"] == 6
    assert r["due"] is False


def test_interval_overdue_negative_days(client, auth_headers):
    r = create_routine(
        client, auth_headers, type="interval", freq_days=7, last_done=iso(10)
    )
    assert r["days_until_due"] == -3
    assert r["due"] is True


def test_interval_checkin_resets_cycle_and_cancel_restores(client, auth_headers):
    r = create_routine(
        client, auth_headers, type="interval", freq_days=7, last_done=iso(10)
    )
    rid = r["id"]

    body = client.post(f"{API}/{rid}/checkin", headers=auth_headers).json()
    assert body["due"] is False
    assert body["days_until_due"] == 7
    assert body["last_done"] == iso(0)

    body = client.delete(f"{API}/{rid}/checkin", headers=auth_headers).json()
    assert body["due"] is True
    assert body["days_until_due"] == -3
    assert body["last_done"] == iso(10)


# ---------- as_needed ----------


def test_as_needed_uses_flow(client, auth_headers):
    r = create_routine(client, auth_headers, type="as_needed", threshold=3)
    rid = r["id"]
    assert r["uses_count"] == 0 and r["due"] is False

    for expected in (1, 2):
        body = client.post(f"{API}/{rid}/uses", headers=auth_headers).json()
        assert body["uses_count"] == expected
        assert body["due"] is False

    body = client.post(f"{API}/{rid}/uses", headers=auth_headers).json()
    assert body["uses_count"] == 3
    assert body["due"] is True  # ครบ threshold = ถึงรอบ

    # −1 แล้วหลุดจากถึงรอบ
    body = client.delete(f"{API}/{rid}/uses", headers=auth_headers).json()
    assert body["uses_count"] == 2 and body["due"] is False


def test_as_needed_uses_floor_at_zero(client, auth_headers):
    rid = create_routine(client, auth_headers, type="as_needed", threshold=3)["id"]
    body = client.delete(f"{API}/{rid}/uses", headers=auth_headers).json()
    assert body["uses_count"] == 0


def test_as_needed_checkin_resets_counter_and_cancel_restores(client, auth_headers):
    rid = create_routine(client, auth_headers, type="as_needed", threshold=3)["id"]
    for _ in range(4):
        client.post(f"{API}/{rid}/uses", headers=auth_headers)

    body = client.post(f"{API}/{rid}/checkin", headers=auth_headers).json()
    assert body["uses_count"] == 0
    assert body["due"] is False and body["done_today"] is True

    # ยกเลิกเช็คอิน → ตัวนับคืนค่าเดิม
    body = client.delete(f"{API}/{rid}/checkin", headers=auth_headers).json()
    assert body["uses_count"] == 4
    assert body["due"] is True and body["done_today"] is False


def test_uses_rejected_for_non_as_needed(client, auth_headers):
    rid = create_routine(client, auth_headers, type="daily")["id"]
    assert client.post(f"{API}/{rid}/uses", headers=auth_headers).status_code == 400
    assert client.delete(f"{API}/{rid}/uses", headers=auth_headers).status_code == 400


# ---------- update / เปลี่ยนประเภทข้ามกัน ----------


def test_switch_daily_to_interval(client, auth_headers):
    rid = create_routine(client, auth_headers, type="daily")["id"]
    res = client.patch(
        f"{API}/{rid}", json={"type": "interval", "freq_days": 14}, headers=auth_headers
    )
    assert res.status_code == 200
    body = res.json()
    assert body["type"] == "interval" and body["freq_days"] == 14
    assert body["streak"] is None and body["last_7_days"] is None


def test_switch_to_interval_without_freq_rejected(client, auth_headers):
    rid = create_routine(client, auth_headers, type="daily")["id"]
    res = client.patch(f"{API}/{rid}", json={"type": "interval"}, headers=auth_headers)
    assert res.status_code == 422


def test_switch_as_needed_to_daily_clears_counter(client, auth_headers):
    rid = create_routine(client, auth_headers, type="as_needed", threshold=3)["id"]
    client.post(f"{API}/{rid}/uses", headers=auth_headers)
    body = client.patch(
        f"{API}/{rid}", json={"type": "daily"}, headers=auth_headers
    ).json()
    assert body["type"] == "daily"
    assert body["threshold"] is None and body["uses_count"] == 0


def test_switch_interval_to_daily_keeps_logs_for_streak(client, auth_headers):
    r = create_routine(
        client, auth_headers, type="interval", freq_days=7, last_done=iso(0)
    )
    body = client.patch(
        f"{API}/{r['id']}", json={"type": "daily"}, headers=auth_headers
    ).json()
    assert body["freq_days"] is None
    assert body["streak"] == 1 and body["done_today"] is True


# ---------- auth + ownership ----------


def test_requires_auth(client):
    assert client.get(API).status_code == 401


def test_cannot_access_other_users_routine(client, auth_headers):
    rid = create_routine(client, auth_headers, type="daily")["id"]
    other = register_and_login(client, email="other@example.com")
    assert client.get(f"{API}/{rid}", headers=other).status_code == 404
    assert client.post(f"{API}/{rid}/checkin", headers=other).status_code == 404
    assert client.delete(f"{API}/{rid}", headers=other).status_code == 404


def test_delete_routine(client, auth_headers):
    rid = create_routine(client, auth_headers, type="daily")["id"]
    client.post(f"{API}/{rid}/checkin", headers=auth_headers)
    assert client.delete(f"{API}/{rid}", headers=auth_headers).status_code == 204
    assert client.get(f"{API}/{rid}", headers=auth_headers).status_code == 404
