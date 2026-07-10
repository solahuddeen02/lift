# Lift

แอพบันทึกทุกอย่างเพื่อใช้ชีวิต — standalone แต่ออกแบบให้ merge เข้าโปรเจกต์ Atlas ได้ในอนาคต
เจ้าของโปรเจกต์: Deen (student, ใช้ภาษาไทยเป็นหลัก — ตอบภาษาไทยได้)

## Stack

- Backend: FastAPI + SQLAlchemy 2.0 + Pydantic v2, JWT auth (PyJWT + passlib pbkdf2_sha256)
- DB: SQLite ตอน dev → Postgres ได้ด้วย env `DATABASE_URL` ตัวเดียว (ห้าม hardcode SQLite-only feature)
- Frontend: React 18 + Vite + Tailwind v4 (`@tailwindcss/vite`)
- Docker Compose (backend + frontend/nginx)

## โครงสร้าง

```
backend/app/core/       # config, database, security(JWT), deps, models(User), auth_routes
backend/app/modules/    # 1 feature = 1 module (tasks/ มีแล้ว: models, schemas, routes)
frontend/src/           # api/client.js, context/AuthContext, pages/, components/
design/prototype-mobile.html   # ⭐ SOURCE OF TRUTH ของ UI — เปิดในเบราว์เซอร์ได้เลย
docs/DESIGN.md          # สเปค UI/UX ละเอียดจาก prototype
```

## กติกา Atlas-ready (ต้องรักษาไว้)

- API prefix `/api/v1/` ทุก route
- ทุก model มี `user_id` (ห้าม single-user)
- Auth เป็น JWT Bearer
- Feature ใหม่ = module ใหม่ใน `backend/app/modules/`

## สถานะปัจจุบัน

- [x] Phase 1 Backend: auth (register/login/me) + tasks CRUD — รันทดสอบแล้ว ใช้งานได้
- [x] Frontend Phase 1 เวอร์ชันแรก (หน้า login + task list) — **ตกรุ่นแล้ว** เทียบกับ prototype ให้ยึด prototype เป็นหลักแล้ว refactor
- [x] Design prototype ครบ 4 หน้า (Dashboard / Tasks / Routine / Journal) — ดู docs/DESIGN.md
- [x] Routine module (daily/interval/as-needed) + pytest 26 ตัว (`cd backend && python -m pytest`)
- [x] Task เพิ่ม note + category (module `categories` แยก, seed 4 หมวด preset ตอน register)
- [x] Frontend หน้า Tasks refactor ตาม prototype แล้ว (app shell + tab bar + bottom sheets)
- [x] Frontend หน้า Routine ครบ 3 ประเภท (tab วันนี้/รายวัน/งานเป็นรอบ + urgency sort + uses counter)
- [x] Journal ครบ backend+frontend (module `journal`, 1 entry/วัน เขียนซ้ำ = แก้, mood 5 แบบ) — pytest รวม 46 ตัว
- [x] Dashboard ครบ backend+frontend (module `dashboard` — GET /api/v1/dashboard สรุปตัวเดียว) — ครบทั้ง 4 หน้าตาม prototype แล้ว 🎉
- [x] เตรียม production: docker-compose.prod.yml (SECRET_KEY บังคับ) + env `REGISTRATION_ENABLED` + docs/DEPLOY.md (Proxmox LXC + cloudflared) — pytest รวม 58 ตัว

## สิ่งสำคัญที่ design เปลี่ยนจาก backend เดิม

1. หน้า "Habits" เปลี่ยนคอนเซ็ปต์เป็น **"Routine"** มี 3 ประเภท (daily / interval / as-needed) — ต้องออกแบบ module ใหม่ ยังไม่มีใน backend
2. Task เพิ่ม field: `note` (text), `category` (งาน/ส่วนตัว/เรียน/บ้าน — ควรเป็นตารางแยกให้ user สร้างเองได้)
3. UI เป็น mobile-first ใช้มือเดียว — ดูรายละเอียดใน docs/DESIGN.md

## รัน dev

```bash
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload   # :8000 (/docs)
cd frontend && npm install && npm run dev                                        # :5173 proxy /api → :8000
```
