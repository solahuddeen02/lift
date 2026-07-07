# Lift — Design Spec (จาก design/prototype-mobile.html)

prototype เปิดในเบราว์เซอร์ได้เลย เป็น source of truth ของ UI ทั้งหมด — เอกสารนี้สรุป logic ที่มองไม่เห็นจากหน้าจอ

## หลักการรวม

- **Mobile-first, ใช้มือเดียว (thumb zone)**: ปุ่มโต้ตอบหลักอยู่ครึ่งล่างจอทั้งหมด
  - Bottom tab bar 4 แท็บ: หน้าหลัก / Tasks / Routine / Journal
  - FAB ＋ (หน้า Tasks และ Routine) เปิด bottom sheet สำหรับเพิ่ม
  - Filter เป็น pill ลอยเหนือ tab bar
  - แก้ไข/ลบ ผ่านปุ่ม ⋯ บนการ์ด → เด้ง action sheet จากล่าง (ลบมี confirm)
  - ทุก sheet เป็น bottom sheet ปุ่มใหญ่
- **Dark minimal**: bg #0a0a0f, surface #14141c, accent indigo #6366f1, green #34d399, red #f87171, yellow #fbbf24
- **ยกเลิกได้ทุก action** (กันกดพลาด): เช็คอินซ้ำ = ยกเลิก, แถวเสร็จแล้วมีปุ่ม "ยกเลิก", ตัวนับมี −1
- **ทำแล้วย่อส่วน**: รายการที่เสร็จวันนี้ยุบเป็นแถวเล็กจาง อยู่กลุ่มล่างสุด

## หน้า Dashboard (หน้าหลัก) — ทุกอย่างกดได้

- วงแหวน progress 2 อัน: Routine วันนี้ (%เขียว, กดไป Routine), Task เสร็จ (%ม่วง, กดไป Tasks)
- กราฟแท่ง 7 วัน: ความสูง = สัดส่วน routine ที่ทำได้/วัน, emoji mood ลอยหัวแท่ง, แท่งวันนี้สีเขียว, มุมขวา 🔥 streak — กดไป Routine
- ลิสต์ "Task ที่ต้องทำ" (3 อันแรก): วงกลมหน้าแถวติ๊กเสร็จได้เลย (ขอบสีตาม priority), แตะชื่อเปิด sheet แก้ไข
- ลิสต์ "Routine วันนี้": แตะทั้งแถว = เช็คอิน/ยกเลิกจากหน้าหลัก
- การ์ด Journal ล่าสุด: แตะไปหน้า Journal

## หน้า Tasks

- Field: title, priority (low/medium/high), due date, note, category
- Category preset 4 หมวดพร้อมสี: งาน #818cf8 / ส่วนตัว #34d399 / เรียน #fbbf24 / บ้าน #f472b6 (ทำจริง: ให้ user จัดการหมวดเองได้)
- **จัดกลุ่มตามเวลา**: เลยกำหนด (หัวแดง) → วันนี้ → พรุ่งนี้ → ถัดไป → ไม่มีกำหนด; ในกลุ่มเรียง priority สูง→ต่ำ
- Filter ลอยแถวเดียว: ปุ่ม 🏷 (เปิด sheet เลือกหมวด, เลือกแล้วปุ่มโชว์จุดสี+ชื่อหมวด) + ทั้งหมด/ค้างอยู่/เสร็จแล้ว
- แตะตัว task = เปิด sheet แก้ไข (มีช่องโน้ต), ⋯ = action sheet แก้ไข/ลบ
- เสร็จแล้วยุบเป็นแถวเล็ก + ปุ่มยกเลิก

## หน้า Routine (เดิมคือ Habits)

3 ประเภท:

| ประเภท | freq | การแสดง | เช็คอิน |
|---|---|---|---|
| รายวัน (daily) | ทุกวัน | streak 🔥 + จุด 7 วัน | ปุ่มเช็คอิน / กดซ้ำยกเลิก (streak คืน) |
| เป็นรอบ (interval) | ทุก N วัน (2,3,4,7,14,30,90,180,365) | "ทำล่าสุด X วัน/เดือน/ปีก่อน" + badge (ถึงรอบแล้ว แดง / อีก X วัน) | ปุ่มทำแล้ว / กดซ้ำยกเลิก |
| ตามสภาพ (as-needed) | นับจากการใช้งาน | แถบ progress uses/threshold + ปุ่ม "＋ ใช้แล้ว 1 ครั้ง" (มี −1) | พอ uses ≥ threshold ปุ่ม ＋ **ถูกแทนที่** ด้วยปุ่มแดง "ทำแล้ววันนี้" → เช็คอินแล้วตัวนับรีเซ็ต 0 |

- ตัวอย่าง as-needed: ซักผ้า (นับจากจำนวนครั้งที่ใส่เสื้อผ้า, threshold 7)
- Segmented tab (pill ลอย): **วันนี้** (default — รายวันที่ยังไม่ทำ + ที่ถึงรอบ, เรียงตาม urgency, เสร็จแล้วย่อส่วน, ว่าง = "วันนี้ครบหมดแล้ว 🎉") / **รายวัน** (การ์ดเต็มทั้งหมด) / **งานเป็นรอบ** (interval+as-needed เรียงใกล้ถึงรอบ)
- Urgency sort: เลยกำหนดมากสุดขึ้นบนสุด (ค่าติดลบ) → ถึงรอบ → รายวัน → ตามวันที่เหลือ
- สร้าง/แก้ไข: ชื่อ + ความถี่ + (interval/as-needed) วันที่ทำล่าสุด "ไม่เลือก = เริ่มแบบถึงรอบ" + (as-needed) stepper "ครบกี่ครั้งถึงรอบ − 7 ＋"
- เปลี่ยนความถี่ข้ามประเภทได้ การ์ดย้ายกลุ่ม/รูปแบบเอง

## หน้า Journal

- Mood picker 5 อัน: 😄 😌 😐 😔 😤 (แถวบน, เลือกแล้ว highlight)
- Textarea + ปุ่มบันทึก, ลิสต์บันทึกก่อนหน้า (วันที่ + mood + ตัวอย่างข้อความ 1 บรรทัด)

## ข้อเสนอ data model (backend ยังไม่มี routine)

```
routines: id, user_id, name, type(daily|interval|as_needed),
          freq_days(null สำหรับ daily/as_needed), threshold(as_needed),
          uses_count(as_needed), created_at
routine_logs: id, routine_id, done_at(date)   # คำนวณ streak/last_done/กราฟ 7 วันจาก log
categories: id, user_id, name, color
tasks: + note(text), category_id(fk nullable)
```
