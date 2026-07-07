# Lift

แอพบันทึกทุกอย่างเพื่อใช้ชีวิต — standalone แต่ออกแบบให้เชื่อม Atlas ได้ในอนาคต

## Phase status

- [x] Phase 1 — Task/Todo (CRUD, due date, priority, status, filter)
- [ ] Phase 2 — Habit Tracker
- [ ] Phase 3 — Journal
- [ ] Phase 4 — Dashboard

## Stack

FastAPI + SQLAlchemy + SQLite (dev) / React + Vite + Tailwind

## รันแบบ dev

Backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

Frontend:

```bash
cd frontend
npm install
npm run dev
```

เปิด http://localhost:5173 (Vite proxy ส่ง `/api` ไป backend ให้อัตโนมัติ)

## รันด้วย Docker

```bash
docker compose up --build
```

เปิด http://localhost:5173

## Atlas-ready design

- JWT auth + `user_id` ในทุก model — ไม่ผูกกับ single user
- API prefix `/api/v1/` ตั้งแต่แรก
- แต่ละ feature เป็น module ใน `backend/app/modules/` — ยกไป mount ใน Atlas ได้
- เปลี่ยน DB เป็น Postgres ได้ด้วย env `DATABASE_URL` ตัวเดียว
