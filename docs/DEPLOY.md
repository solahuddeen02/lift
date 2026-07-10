# Deploy Lift บน Proxmox LXC + Cloudflare Tunnel

ภาพรวม: LXC (Debian 12) → Docker Compose (nginx serve frontend + proxy `/api` → backend)
→ cloudflared เชื่อม tunnel ออก Cloudflare → เข้าจากที่ไหนก็ได้ผ่านโดเมนตัวเอง
**ไม่ต้องเปิด port forward ใดๆ ที่ router** — cloudflared ต่อออกอย่างเดียว (outbound only)

```
[มือถือ/เบราว์เซอร์] → Cloudflare → tunnel → cloudflared (ใน LXC)
                                              → 127.0.0.1:8080 (nginx)
                                                 ├─ /            → frontend (React build)
                                                 ├─ /api/…       → backend :8000
                                                 └─ /health      → backend :8000
```

## 1. สร้าง LXC บน Proxmox

- Template: **Debian 12** (standard)
- Spec แนะนำ: 2 vCPU / 1 GB RAM / 8 GB disk (เหลือเฟือสำหรับใช้คนเดียว)
- **Unprivileged container** + เปิด **nesting** (จำเป็นสำหรับ Docker):
  - ตอนสร้าง: Options → Features → ติ๊ก `nesting=1`
  - หรือหลังสร้าง: `pct set <CTID> --features nesting=1` แล้ว restart container

### ทางเลือก: ใช้ VM แทน LXC

ถ้า RAM เหลือและอยากตัดปัญหา Docker-in-LXC ทิ้งไปเลย (nesting, overlayfs งอแงหลัง
Proxmox upgrade) ให้สร้างเป็น **VM** แทน — ขั้นตอนที่เหลือทั้งหมด (ข้อ 2 เป็นต้นไป) เหมือนเดิมทุกอย่าง:

- สร้าง VM จาก **Debian 12 ISO** ติดตั้ง OS ตามปกติ
- Spec แนะนำ: 2 vCPU / 2 GB RAM / 20 GB disk (VM กิน overhead มากกว่า LXC)
- **ไม่ต้องยุ่งกับ nesting** — Docker รันเนทีฟใน VM ได้เลย
- ข้อแลกเปลี่ยน: กิน RAM/disk มากกว่า boot ช้ากว่า แต่ isolation เต็มตัวและเสถียรกว่าในระยะยาว

สรุปสั้น: เครื่องสเปคจำกัด → LXC / อยากจบไม่ต้องดูแลอะไรเพิ่ม → VM

## 2. ติดตั้ง Docker ใน LXC

```bash
apt update && apt upgrade -y
apt install -y curl git ca-certificates
curl -fsSL https://get.docker.com | sh
docker --version && docker compose version   # เช็คว่ามาครบ
```

## 3. เอาโค้ดขึ้นและตั้งค่า

```bash
git clone <URL repo ของเรา> /opt/lift
cd /opt/lift

# สร้าง .env จากตัวอย่าง
cp .env.example .env
openssl rand -hex 32   # copy ผลลัพธ์ไปใส่ SECRET_KEY ใน .env
nano .env
```

`.env` ครั้งแรกควรเป็น:

```env
SECRET_KEY=<ค่าที่ generate เมื่อกี้>
REGISTRATION_ENABLED=true
```

> ⚠️ `SECRET_KEY` เป็น field บังคับ — ถ้าไม่ตั้ง compose จะไม่ยอม start เลย (ตั้งใจให้เป็นแบบนั้น)
> และห้ามเปลี่ยนทีหลังโดยไม่จำเป็น เพราะ token ที่ login ค้างไว้จะหลุดหมด

## 4. รัน

```bash
docker compose -f docker-compose.prod.yml up -d --build

# เช็คว่าตื่นครบ
docker compose -f docker-compose.prod.yml ps
curl http://127.0.0.1:8080/health        # → {"status":"ok","app":"Lift"}
```

ข้อมูลทั้งหมด (SQLite) อยู่ใน named volume `lift-data` — `docker compose down` ได้โดยข้อมูลไม่หาย
(อย่าใช้ `down -v` เด็ดขาด นั่นคือลบ volume)

## 5. ต่อ Cloudflare Tunnel

ต้องมีโดเมนที่ใช้ Cloudflare เป็น DNS อยู่แล้ว — วิธีที่ง่ายที่สุดคือแบบจัดการผ่าน dashboard:

1. เข้า [one.dash.cloudflare.com](https://one.dash.cloudflare.com) → **Networks → Tunnels → Create a tunnel** (แบบ Cloudflared)
2. ตั้งชื่อ เช่น `lift` → Cloudflare จะโชว์คำสั่งติดตั้งพร้อม token — เลือกแบบ Debian แล้ว copy มารันใน LXC:

```bash
# คำสั่งจริงจะมี token ต่อท้าย — copy จาก dashboard
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared.deb
cloudflared service install <TOKEN>
```

3. หน้า **Public Hostname** ของ tunnel: เพิ่ม hostname
   - Subdomain/Domain: เช่น `lift.example.com`
   - Service: **HTTP** → `localhost:8080`
4. เสร็จ — เปิด `https://lift.example.com` ได้เลย (Cloudflare จัดการ HTTPS ให้)

cloudflared ติดตั้งเป็น systemd service แล้ว รีบูต LXC ก็กลับมาเอง (`systemctl status cloudflared`)

> แนะนำเพิ่ม: ใน Zero Trust ตั้ง **Access policy** ครอบ hostname นี้ (เช่น require email ตัวเอง)
> จะได้มีด่านของ Cloudflare อีกชั้นก่อนถึงหน้า login ของแอพ

## 6. สมัคร user แรก แล้วปิดรับสมัคร

1. เปิดเว็บ → สมัครบัญชีของเรา
2. ปิดรับสมัคร:

```bash
cd /opt/lift
sed -i 's/REGISTRATION_ENABLED=true/REGISTRATION_ENABLED=false/' .env
docker compose -f docker-compose.prod.yml up -d   # recreate backend ให้อ่านค่าใหม่
```

หลังจากนี้ `POST /api/v1/auth/register` จะตอบ 403 — login ปกติใช้ได้เหมือนเดิม

## 7. อัปเดตเวอร์ชัน

```bash
cd /opt/lift
git pull
docker compose -f docker-compose.prod.yml up -d --build
docker image prune -f   # เก็บกวาด image เก่า
```

## 8. Backup

ข้อมูลจริงมีไฟล์เดียวคือ SQLite ใน volume:

```bash
# ดึงไฟล์ DB ออกมา (ทำตอนไหนก็ได้ ไม่ต้องหยุด service)
docker compose -f docker-compose.prod.yml cp backend:/data/lift.db /root/backup-lift-$(date +%F).db
```

ตั้ง cron รายวันง่ายๆ: `crontab -e`

```cron
0 3 * * * cd /opt/lift && docker compose -f docker-compose.prod.yml cp backend:/data/lift.db /root/backups/lift-$(date +\%F).db
```

และเปิด **Proxmox backup (vzdump)** ของทั้ง LXC ไว้อีกชั้นจาก host ก็ครอบคลุมสุด

ส่วนการ**ย้ายเครื่อง** (LXC → VM, เปลี่ยน server, กู้จาก backup) ดู [MIGRATE.md](MIGRATE.md)

## Troubleshooting

| อาการ | เช็ค |
|---|---|
| compose ไม่ start บ่นเรื่อง SECRET_KEY | ยังไม่ได้สร้าง `.env` หรือค่าว่าง — ดูข้อ 3 |
| เว็บเปิดได้แต่ API error | `docker compose -f docker-compose.prod.yml logs backend` |
| tunnel ไม่ติด | `systemctl status cloudflared` + ดูสถานะ tunnel ใน dashboard |
| Docker ใน LXC ไม่ยอมรัน | ลืมเปิด `nesting=1` — ดูข้อ 1 |
