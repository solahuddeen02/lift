# ย้ายเครื่อง / ย้ายข้อมูล

ข้อมูลจริงทั้งระบบของ Lift มี **ไฟล์เดียว**: SQLite ที่ `/data/lift.db` ใน Docker volume `lift-data`
frontend ไม่มี state, image ทั้งหมด rebuild จาก git ได้เสมอ — สิ่งที่ต้องหอบไปมีแค่ 2 อย่าง:

1. **`lift.db`** — ตัวข้อมูล
2. **`.env`** — เพราะ `SECRET_KEY` ใช้เซ็น JWT: ถ้าเครื่องใหม่ใช้ key คนละตัว
   ข้อมูลไม่หายแต่ทุก session ที่ login ค้างไว้จะหลุด (ต้อง login ใหม่) — ใช้ `.env` เดิมแล้วย้ายแบบเนียน

ใช้ได้กับทุกกรณี: LXC → VM, ย้าย server, กู้จาก backup

## เครื่องเก่า — ดึงของออก

```bash
cd /opt/lift
docker compose -f docker-compose.prod.yml stop backend   # หยุดก่อน copy กัน DB เขียนค้าง
docker compose -f docker-compose.prod.yml cp backend:/data/lift.db ./lift.db
docker compose -f docker-compose.prod.yml start backend  # เปิดกลับ ใช้ต่อได้ระหว่างเซ็ตเครื่องใหม่

scp lift.db .env root@<เครื่องใหม่>:/opt/lift/
```

> `docker cp` ทำงานกับ container ที่ stop อยู่ได้ — หยุดแค่ backend ตัวเดียวไม่กี่วินาที
> ปลอดภัยกว่า copy ทั้งที่ DB ยังถูกเขียนอยู่

## เครื่องใหม่ — เอาของเข้า

เตรียมเครื่องตาม [DEPLOY.md](DEPLOY.md) ข้อ 1–2 ก่อน (LXC/VM + Docker) แล้ว:

```bash
git clone <URL repo> /opt/lift
cd /opt/lift               # วาง .env ที่ scp มาไว้ที่นี่

docker compose -f docker-compose.prod.yml up -d --build   # start ครั้งแรก สร้าง volume เปล่า
docker compose -f docker-compose.prod.yml stop backend
docker compose -f docker-compose.prod.yml cp ./lift.db backend:/data/lift.db   # ทับ DB เปล่า
docker compose -f docker-compose.prod.yml start backend

curl http://127.0.0.1:8080/health   # แล้วลอง login เช็คข้อมูลเดิม
```

## ย้าย Cloudflare Tunnel

ฝั่ง Cloudflare **ไม่ต้องแตะอะไร** — ติดตั้ง cloudflared บนเครื่องใหม่ด้วย **token เดิม**
(ดูได้จาก dashboard หน้า tunnel):

```bash
cloudflared service install <TOKEN>
```

พอ connector เครื่องใหม่ขึ้นใน dashboard ก็ปิด cloudflared เครื่องเก่า — โดเมนเดิมชี้มาเครื่องใหม่ทันที

**ลำดับที่ downtime ต่ำสุด**: เซ็ตเครื่องใหม่ให้เสร็จก่อน → ย้าย DB รอบสุดท้าย → สลับ cloudflared

## ข้อควรระวัง

- **อย่าใช้ `docker compose down -v`** — `-v` คือลบ volume = ลบ DB ทิ้ง
- ชื่อ volume จริงบน host คือ `lift_lift-data` (prefix ตามชื่อโฟลเดอร์โปรเจกต์) —
  ถ้า clone ไว้คนละชื่อโฟลเดอร์จะเป็นคนละ volume ไม่ใช่ปัญหาถ้าย้ายผ่าน `compose cp` ตามสูตรข้างบน
- ตอน copy ต้องไม่มีไฟล์ `lift.db-wal` / `lift.db-shm` ค้างข้างๆ (หยุด backend ก่อนตามสูตร = ไม่มี)

## อนาคต: SQLite → Postgres (ตอน merge เข้า Atlas)

โค้ดพร้อมแล้ว — เปลี่ยน `DATABASE_URL` ตัวเดียว ไม่มี SQLite-only feature
แต่**ตัวข้อมูล**ต้องแปลงด้วยเครื่องมือ เช่น:

```bash
pgloader lift.db postgresql://user:pass@host/lift
```

แล้วตรวจ sequence ของ id ให้ต่อเลขถูก — ค่อยว่ากันตอนถึงเวลา ไม่ต้องเตรียมอะไรตอนนี้
