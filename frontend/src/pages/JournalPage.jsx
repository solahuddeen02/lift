import { useEffect, useState } from "react";
import { api } from "../api/client.js";

const MOODS = ["😄", "😌", "😐", "😔", "😤"];

/* ใช้วันที่ท้องถิ่นของเครื่อง user เป็นหลัก (backend รับ entry_date จาก client) */
function localISO() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
    d.getDate()
  ).padStart(2, "0")}`;
}

function dateLabel(iso) {
  const d0 = new Date();
  d0.setHours(0, 0, 0, 0);
  const d1 = new Date(iso);
  d1.setHours(0, 0, 0, 0);
  const diff = Math.round((d0 - d1) / 864e5);
  if (diff <= 0) return "วันนี้";
  if (diff === 1) return "เมื่อวาน";
  if (diff < 7) return `${diff} วันก่อน`;
  return d1.toLocaleDateString("th-TH", { day: "numeric", month: "short" });
}

export default function JournalPage() {
  const [entries, setEntries] = useState([]);
  const [mood, setMood] = useState(null);
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const todayEntry = entries.find((e) => e.entry_date === localISO());

  async function load({ prefill = false } = {}) {
    try {
      const list = await api.listJournal();
      setEntries(list);
      setError("");
      if (prefill) {
        const today = list.find((e) => e.entry_date === localISO());
        if (today) {
          setMood(today.mood);
          setText(today.text);
        }
      }
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load({ prefill: true });
  }, []);

  async function save() {
    if (!text.trim() || busy) return;
    setBusy(true);
    try {
      // ไม่เลือก mood = 😐 ตาม prototype; เขียนซ้ำวันเดิม = แก้ของวันนั้น
      await api.upsertJournal({
        mood: mood || "😐",
        text: text.trim(),
        entry_date: localISO(),
      });
      if (!mood) setMood("😐");
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="h-full animate-fadein overflow-y-auto px-4 pt-10 pb-44">
      <div className="text-[26px] font-bold">Journal</div>
      <div className="mb-5 mt-0.5 text-[13px] text-dim">วันนี้รู้สึกยังไง?</div>

      {error && <p className="mb-4 text-sm text-red">{error}</p>}

      <div className="mb-3.5 flex justify-between gap-2">
        {MOODS.map((m) => (
          <button
            key={m}
            onClick={() => setMood(m)}
            className={`flex aspect-square max-w-15 flex-1 items-center justify-center rounded-2xl border text-2xl transition ${
              mood === m
                ? "border-accent bg-accent/15 grayscale-0"
                : "border-line bg-surface2 grayscale-[.7]"
            }`}
          >
            {m}
          </button>
        ))}
      </div>

      <textarea
        placeholder="วันนี้เป็นยังไงบ้าง…"
        value={text}
        onChange={(e) => setText(e.target.value)}
        className="mb-3 min-h-35 w-full resize-none rounded-2xl border border-line bg-surface p-3.5 text-sm leading-relaxed text-ink outline-none placeholder:text-faint focus:border-accent"
      />
      <button
        onClick={save}
        disabled={busy || !text.trim()}
        className="w-full rounded-xl bg-accent py-3.5 text-[15px] font-semibold text-white disabled:opacity-50"
      >
        บันทึก
      </button>
      {todayEntry && (
        <p className="mt-2 text-center text-[11px] text-faint">
          ✓ บันทึกของวันนี้แล้ว — เขียนซ้ำจะแก้ของวันนี้
        </p>
      )}

      <div className="mt-4 rounded-2xl border border-line bg-surface p-4">
        <h3 className="mb-1 text-[13px] font-semibold text-dim">บันทึกก่อนหน้า</h3>
        {entries.length === 0 && (
          <div className="py-4 text-center text-[13px] text-faint">ยังไม่มีบันทึก</div>
        )}
        {entries.map((e) => (
          <div key={e.id} className="border-b border-line py-3 last:border-b-0 last:pb-0">
            <div className="mb-1 flex justify-between text-[11px] text-dim">
              <span>{dateLabel(e.entry_date)}</span>
              <span>{e.mood}</span>
            </div>
            <div className="truncate text-[13px]">{e.text}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
