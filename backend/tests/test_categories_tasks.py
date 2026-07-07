from tests.conftest import register_and_login

CATS = "/api/v1/categories"
TASKS = "/api/v1/tasks"


def get_categories(client, headers):
    res = client.get(CATS, headers=headers)
    assert res.status_code == 200
    return res.json()


# ---------- categories ----------


def test_register_seeds_default_categories(client, auth_headers):
    cats = get_categories(client, auth_headers)
    assert [(c["name"], c["color"]) for c in cats] == [
        ("งาน", "#818cf8"),
        ("ส่วนตัว", "#34d399"),
        ("เรียน", "#fbbf24"),
        ("บ้าน", "#f472b6"),
    ]


def test_create_update_delete_category(client, auth_headers):
    res = client.post(
        CATS, json={"name": "ฟิตเนส", "color": "#00ff00"}, headers=auth_headers
    )
    assert res.status_code == 201
    cid = res.json()["id"]

    res = client.patch(f"{CATS}/{cid}", json={"name": "สุขภาพ"}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "สุขภาพ"
    assert res.json()["color"] == "#00ff00"

    assert client.delete(f"{CATS}/{cid}", headers=auth_headers).status_code == 204
    assert all(c["id"] != cid for c in get_categories(client, auth_headers))


def test_category_color_must_be_hex(client, auth_headers):
    res = client.post(CATS, json={"name": "x", "color": "แดง"}, headers=auth_headers)
    assert res.status_code == 422


def test_categories_isolated_per_user(client, auth_headers):
    cid = get_categories(client, auth_headers)[0]["id"]
    other = register_and_login(client, email="other@example.com")
    # user อื่นเห็นแต่ preset ของตัวเอง แตะของคนอื่นไม่ได้
    assert all(c["id"] != cid for c in get_categories(client, other))
    assert client.patch(f"{CATS}/{cid}", json={"name": "x"}, headers=other).status_code == 404
    assert client.delete(f"{CATS}/{cid}", headers=other).status_code == 404


# ---------- task note + category ----------


def test_task_with_note_and_category(client, auth_headers):
    cid = get_categories(client, auth_headers)[0]["id"]
    res = client.post(
        TASKS,
        json={"title": "ทำการบ้าน", "note": "บทที่ 3-4", "category_id": cid},
        headers=auth_headers,
    )
    assert res.status_code == 201
    body = res.json()
    assert body["note"] == "บทที่ 3-4"
    assert body["category_id"] == cid


def test_task_note_defaults_empty(client, auth_headers):
    res = client.post(TASKS, json={"title": "งานเปล่า"}, headers=auth_headers)
    assert res.status_code == 201
    assert res.json()["note"] == ""
    assert res.json()["category_id"] is None


def test_task_rejects_other_users_category(client, auth_headers):
    other = register_and_login(client, email="other@example.com")
    other_cid = get_categories(client, other)[0]["id"]
    res = client.post(
        TASKS, json={"title": "x", "category_id": other_cid}, headers=auth_headers
    )
    assert res.status_code == 404


def test_task_patch_note_and_clear_category(client, auth_headers):
    cid = get_categories(client, auth_headers)[0]["id"]
    tid = client.post(
        TASKS, json={"title": "x", "category_id": cid}, headers=auth_headers
    ).json()["id"]

    res = client.patch(
        f"{TASKS}/{tid}", json={"note": "เพิ่มโน้ต", "category_id": None}, headers=auth_headers
    )
    assert res.status_code == 200
    assert res.json()["note"] == "เพิ่มโน้ต"
    assert res.json()["category_id"] is None


def test_list_tasks_filter_by_category(client, auth_headers):
    cats = get_categories(client, auth_headers)
    work, home = cats[0]["id"], cats[3]["id"]
    client.post(TASKS, json={"title": "งานออฟฟิศ", "category_id": work}, headers=auth_headers)
    client.post(TASKS, json={"title": "ล้างจาน", "category_id": home}, headers=auth_headers)

    res = client.get(TASKS, params={"category_id": home}, headers=auth_headers)
    assert [t["title"] for t in res.json()] == ["ล้างจาน"]


def test_delete_category_unlinks_tasks(client, auth_headers):
    cid = get_categories(client, auth_headers)[0]["id"]
    tid = client.post(
        TASKS, json={"title": "x", "category_id": cid}, headers=auth_headers
    ).json()["id"]

    assert client.delete(f"{CATS}/{cid}", headers=auth_headers).status_code == 204
    task = client.get(f"{TASKS}/{tid}", headers=auth_headers).json()
    assert task["category_id"] is None  # task ยังอยู่ แค่กลายเป็นไม่ระบุหมวด
