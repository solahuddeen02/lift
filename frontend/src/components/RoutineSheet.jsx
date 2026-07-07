import { useEffect, useState } from "react";
import BottomSheet from "./BottomSheet.jsx";

const inputCls =
  "w-full rounded-xl border border-line bg-surface2 px-3.5 py-3 text-sm text-ink outline-none [color-scheme:dark] placeholder:text-faint focus:border-accent";

/* ค่า select เดียวคุมประเภท: "1"=daily, "0"=as_needed, อื่นๆ=interval ทุก N วัน */
const FREQ_OPTIONS = [
  ["1", "ทำทุกวัน"],
  ["2", "ทุก 2 วัน"],
  ["3", "ทุก 3 วัน"],
  ["4", "ทุก 4 วัน"],
  ["7", "ทุกสัปดาห์"],
  ["14", "ทุก 2 สัปดาห์"],
  ["30", "ทุกเดือน"],
  ["90", "ทุก 3 เดือน"],
  ["180", "ทุก 6 เดือน"],
  ["365", "ทุกปี"],
  ["0", "ตามสภาพ (นับจากการใช้งาน)"],
];

function routineToFreq(r) {
  if (r.type === "daily") return "1";
  if (r.type === "as_needed") return "0";
  return String(r.freq_days);
}

/* sheet เพิ่ม/แก้ไข routine — routine=null คือเพิ่มใหม่ */
export default function RoutineSheet({ open, routine, onClose, onSave }) {
  const [name, setName] = useState("");
  const [freq, setFreq] = useState("1");
  const [lastDone, setLastDone] = useState("");
  const [threshold, setThreshold] = useState(7);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!open) return;
    setName(routine?.name ?? "");
    setFreq(routine ? routineToFreq(routine) : "1");
    setThreshold(routine?.threshold ?? 7);
    setLastDone("");
  }, [open, routine]);

  const isEdit = routine != null;
  const isDaily = freq === "1";
  const isAsNeeded = freq === "0";

  async function submit() {
    if (!name.trim() || busy) return;
    const data = { name: name.trim() };
    if (isDaily) data.type = "daily";
    else if (isAsNeeded) {
      data.type = "as_needed";
      data.threshold = threshold;
    } else {
      data.type = "interval";
      data.freq_days = Number(freq);
    }
    // เลือกวันที่ทำล่าสุดได้เฉพาะตอนสร้าง (backend seed log ให้)
    if (!isEdit && !isDaily && lastDone) data.last_done = lastDone;

    setBusy(true);
    try {
      await onSave(data);
    } finally {
      setBusy(false);
    }
  }

  return (
    <BottomSheet
      open={open}
      onClose={onClose}
      title={isEdit ? "แก้ไข Routine" : "เพิ่ม Routine ใหม่"}
    >
      <input
        type="text"
        placeholder="ชื่อ routine…"
        value={name}
        onChange={(e) => setName(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && submit()}
        autoFocus
        className={`${inputCls} mb-2.5`}
      />
      <select value={freq} onChange={(e) => setFreq(e.target.value)} className={`${inputCls} mb-2.5`}>
        {FREQ_OPTIONS.map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>

      {!isEdit && !isDaily && (
        <div className="mb-2.5">
          <div className="mb-1.5 px-0.5 text-xs text-dim">
            ทำล่าสุดเมื่อ (ไม่เลือก = เริ่มแบบถึงรอบเลย)
          </div>
          <input
            type="date"
            value={lastDone}
            onChange={(e) => setLastDone(e.target.value)}
            className={inputCls}
          />
        </div>
      )}

      {isAsNeeded && (
        <div className="mb-2.5 flex items-center justify-between rounded-xl border border-line bg-surface2 px-3.5 py-2.5">
          <span className="text-[13px] text-dim">ครบกี่ครั้งถึงรอบ</span>
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setThreshold((v) => Math.max(1, v - 1))}
              className="size-8.5 rounded-[10px] border border-line bg-surface text-base text-ink active:border-accent active:text-accent"
            >
              −
            </button>
            <span className="min-w-11 text-center text-base font-bold">
              {threshold}
              <span className="ml-0.5 text-[11px] font-normal text-faint">ครั้ง</span>
            </span>
            <button
              type="button"
              onClick={() => setThreshold((v) => v + 1)}
              className="size-8.5 rounded-[10px] border border-line bg-surface text-base text-ink active:border-accent active:text-accent"
            >
              ＋
            </button>
          </div>
        </div>
      )}

      <button
        onClick={submit}
        disabled={busy || !name.trim()}
        className="w-full rounded-xl bg-accent py-3.5 text-[15px] font-semibold text-white disabled:opacity-50"
      >
        {isEdit ? "บันทึก" : "เพิ่ม"}
      </button>
    </BottomSheet>
  );
}
