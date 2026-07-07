from datetime import timedelta

from app.modules.routines import service
from tests.conftest import register_and_login

API = "/api/v1/journal"


def iso(days_ago: int) -> str:
    # ใช้วันเดียวกับ server (UTC) กัน flaky ช่วงหลังเที่ยงคืน
    return (service.today() - timedelta(days=days_ago)).isoformat()


def write(client, headers, **overrides):
    payload = {"mood": "😌", "text": "วันนี้โอเค", **overrides}
    res = client.post(API, json=payload, headers=headers)
    assert res.status_code == 200, res.text
    return res.json()


def test_create_entry_today(client, auth_headers):
    e = write(client, auth_headers, mood="😄", text="วันแรกของ journal")
    assert e["entry_date"] == iso(0)
    assert e["mood"] == "😄"
    assert e["text"] == "วันแรกของ journal"


def test_write_again_same_day_updates_not_duplicates(client, auth_headers):
    first = write(client, auth_headers, mood="😐", text="ร่างแรก")
    second = write(client, auth_headers, mood="😄", text="แก้แล้ว")

    assert second["id"] == first["id"]  # entry เดิม ไม่สร้างใหม่
    assert second["mood"] == "😄"
    assert second["text"] == "แก้แล้ว"

    entries = client.get(API, headers=auth_headers).json()
    assert len(entries) == 1


def test_explicit_entry_date_backfill(client, auth_headers):
    e = write(client, auth_headers, entry_date=iso(3), text="ย้อนหลัง 3 วัน")
    assert e["entry_date"] == iso(3)


def test_entries_listed_newest_first_with_limit(client, auth_headers):
    for days_ago in (5, 1, 3):
        write(client, auth_headers, entry_date=iso(days_ago), text=f"วัน -{days_ago}")

    entries = client.get(API, headers=auth_headers).json()
    assert [e["entry_date"] for e in entries] == [iso(1), iso(3), iso(5)]

    limited = client.get(API, params={"limit": 2}, headers=auth_headers).json()
    assert len(limited) == 2
    assert limited[0]["entry_date"] == iso(1)


def test_mood_must_be_one_of_five(client, auth_headers):
    res = client.post(
        API, json={"mood": "🤖", "text": "x"}, headers=auth_headers
    )
    assert res.status_code == 422


def test_text_required(client, auth_headers):
    res = client.post(API, json={"mood": "😄", "text": ""}, headers=auth_headers)
    assert res.status_code == 422


def test_far_future_date_rejected(client, auth_headers):
    # เผื่อ +1 วันให้ timezone ที่ล้ำหน้า UTC แต่เกินกว่านั้นไม่ได้
    ok = client.post(
        API, json={"mood": "😄", "text": "x", "entry_date": iso(-1)}, headers=auth_headers
    )
    assert ok.status_code == 200
    bad = client.post(
        API, json={"mood": "😄", "text": "x", "entry_date": iso(-2)}, headers=auth_headers
    )
    assert bad.status_code == 422


def test_delete_entry(client, auth_headers):
    e = write(client, auth_headers)
    assert client.delete(f"{API}/{e['id']}", headers=auth_headers).status_code == 204
    assert client.get(API, headers=auth_headers).json() == []


def test_journal_isolated_per_user(client, auth_headers):
    e = write(client, auth_headers, text="ของฉัน")
    other = register_and_login(client, email="other@example.com")

    assert client.get(API, headers=other).json() == []
    assert client.delete(f"{API}/{e['id']}", headers=other).status_code == 404
    # user อื่นเขียนวันเดียวกันได้ ไม่ชน unique ข้าม user
    write(client, other, text="ของอีกคน")


def test_requires_auth(client):
    assert client.get(API).status_code == 401
