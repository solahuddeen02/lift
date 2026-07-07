from datetime import timedelta

from app.modules.routines import service
from tests.conftest import register_and_login

API = "/api/v1/dashboard"
ROUTINES = "/api/v1/routines"
TASKS = "/api/v1/tasks"
JOURNAL = "/api/v1/journal"


def iso(days_ago: int) -> str:
    return (service.today() - timedelta(days=days_ago)).isoformat()


def dash(client, headers):
    res = client.get(API, headers=headers)
    assert res.status_code == 200, res.text
    return res.json()


def make_routine(client, headers, **overrides):
    payload = {"name": "r", "type": "daily", **overrides}
    res = client.post(ROUTINES, json=payload, headers=headers)
    assert res.status_code == 201
    return res.json()


def test_empty_dashboard(client, auth_headers):
    d = dash(client, auth_headers)
    assert d["routines_today"] == {"done": 0, "total": 0, "items": []}
    assert d["tasks"]["done"] == 0 and d["tasks"]["total"] == 0 and d["tasks"]["top"] == []
    assert len(d["week"]) == 7
    assert all(w["done"] == 0 and w["total"] == 0 and w["mood"] is None for w in d["week"])
    assert d["best_streak"] == 0
    assert d["latest_journal"] is None


def test_routines_today_counts_daily_and_due(client, auth_headers):
    make_routine(client, auth_headers, name="วิ่ง", type="daily")
    make_routine(client, auth_headers, name="ตัดผม", type="interval", freq_days=30)  # ไม่เคยทำ = ถึงรอบ
    make_routine(
        client, auth_headers, name="ล้างแอร์", type="interval", freq_days=180, last_done=iso(1)
    )  # ยังไม่ถึงรอบ — ไม่นับ

    d = dash(client, auth_headers)
    assert d["routines_today"]["total"] == 2
    assert d["routines_today"]["done"] == 0
    assert {r["name"] for r in d["routines_today"]["items"]} == {"วิ่ง", "ตัดผม"}


def test_checked_in_routine_still_listed_as_done(client, auth_headers):
    r = make_routine(client, auth_headers, name="ตัดผม", type="interval", freq_days=30)
    client.post(f"{ROUTINES}/{r['id']}/checkin", headers=auth_headers)

    d = dash(client, auth_headers)
    # เช็คอินแล้วหายจาก due แต่ยังอยู่ในลิสต์วันนี้ (ให้ยกเลิกได้จากหน้าหลัก)
    assert d["routines_today"] == {
        "done": 1,
        "total": 1,
        "items": d["routines_today"]["items"],
    }
    assert d["routines_today"]["items"][0]["done_today"] is True
    assert d["week"][6]["done"] == 1 and d["week"][6]["total"] == 1


def test_week_chart_history_and_mood(client, auth_headers):
    r = make_routine(client, auth_headers, name="วิ่ง", type="daily")
    for days_ago in (2, 1):
        client.post(
            f"{ROUTINES}/{r['id']}/checkin", json={"date": iso(days_ago)}, headers=auth_headers
        )
    client.post(
        JOURNAL,
        json={"mood": "😄", "text": "ดีมาก", "entry_date": iso(1)},
        headers=auth_headers,
    )

    week = dash(client, auth_headers)["week"]
    assert [w["date"] for w in week] == [iso(i) for i in range(6, -1, -1)]
    by_date = {w["date"]: w for w in week}
    assert by_date[iso(2)] == {"date": iso(2), "done": 1, "total": 1, "mood": None}
    assert by_date[iso(1)]["done"] == 1 and by_date[iso(1)]["mood"] == "😄"
    assert by_date[iso(0)]["done"] == 0  # วันนี้ยังไม่เช็คอิน


def test_best_streak_is_max_across_dailies(client, auth_headers):
    r1 = make_routine(client, auth_headers, name="a", type="daily")
    r2 = make_routine(client, auth_headers, name="b", type="daily")
    for days_ago in (2, 1, 0):
        client.post(f"{ROUTINES}/{r1['id']}/checkin", json={"date": iso(days_ago)}, headers=auth_headers)
    client.post(f"{ROUTINES}/{r2['id']}/checkin", headers=auth_headers)

    assert dash(client, auth_headers)["best_streak"] == 3


def test_tasks_top3_sorted_by_group_then_priority(client, auth_headers):
    def task(title, prio, days):
        payload = {"title": title, "priority": prio}
        if days is not None:
            payload["due_date"] = f"{iso(days)}T00:00:00Z"
        assert client.post(TASKS, json=payload, headers=auth_headers).status_code == 201

    task("ไม่มีกำหนด-high", "high", None)
    task("วันนี้-low", "low", 0)
    task("วันนี้-high", "high", 0)
    task("เลยกำหนด-medium", "medium", 2)

    d = dash(client, auth_headers)
    assert d["tasks"]["total"] == 4 and d["tasks"]["done"] == 0
    assert [t["title"] for t in d["tasks"]["top"]] == [
        "เลยกำหนด-medium",
        "วันนี้-high",
        "วันนี้-low",
    ]


def test_task_done_count(client, auth_headers):
    tid = client.post(TASKS, json={"title": "x"}, headers=auth_headers).json()["id"]
    client.post(TASKS, json={"title": "y"}, headers=auth_headers)
    client.patch(f"{TASKS}/{tid}", json={"status": "done"}, headers=auth_headers)

    d = dash(client, auth_headers)
    assert d["tasks"]["done"] == 1 and d["tasks"]["total"] == 2
    assert [t["title"] for t in d["tasks"]["top"]] == ["y"]


def test_latest_journal(client, auth_headers):
    client.post(JOURNAL, json={"mood": "😐", "text": "เก่า", "entry_date": iso(3)}, headers=auth_headers)
    client.post(JOURNAL, json={"mood": "😌", "text": "ใหม่สุด", "entry_date": iso(1)}, headers=auth_headers)

    latest = dash(client, auth_headers)["latest_journal"]
    assert latest["text"] == "ใหม่สุด" and latest["mood"] == "😌"


def test_dashboard_isolated_per_user(client, auth_headers):
    make_routine(client, auth_headers, name="ของฉัน", type="daily")
    other = register_and_login(client, email="other@example.com")
    d = dash(client, other)
    assert d["routines_today"]["total"] == 0


def test_requires_auth(client):
    assert client.get(API).status_code == 401
