import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import ActionSheet from "../components/ActionSheet.jsx";
import RoutineSheet from "../components/RoutineSheet.jsx";

const TABS = [
  { key: "today", label: "วันนี้" },
  { key: "daily", label: "รายวัน" },
  { key: "cycle", label: "งานเป็นรอบ" },
];

const DAY_NAMES = ["อา", "จ", "อ", "พ", "พฤ", "ศ", "ส"];

function freqLabel(r) {
  if (r.type === "as_needed") return "ตามสภาพ";
  const f = r.freq_days;
  if (f === 7) return "ทุกสัปดาห์";
  if (f === 14) return "ทุก 2 สัปดาห์";
  if (f === 30) return "ทุกเดือน";
  if (f % 365 === 0) return f === 365 ? "ทุกปี" : `ทุก ${f / 365} ปี`;
  if (f % 30 === 0) return `ทุก ${f / 30} เดือน`;
  return `ทุก ${f} วัน`;
}

function daysSince(dateStr) {
  const d0 = new Date();
  d0.setHours(0, 0, 0, 0);
  const d1 = new Date(dateStr);
  d1.setHours(0, 0, 0, 0);
  return Math.round((d0 - d1) / 864e5);
}

function lastDoneLabel(r) {
  if (r.done_today) return "วันนี้";
  if (!r.last_done) return "ยังไม่เคยบันทึก";
  const d = daysSince(r.last_done);
  if (d <= 0) return "วันนี้";
  if (d >= 365) return `${Math.floor(d / 365)} ปีก่อน`;
  if (d >= 60) return `${Math.floor(d / 30)} เดือนก่อน`;
  if (d >= 30) return "1 เดือนก่อน";
  return `${d} วันก่อน`;
}

function remainLabel(d) {
  if (d >= 60) return `อีก ~${Math.round(d / 30)} เดือน`;
  return `อีก ${d} วัน`;
}

/* คะแนนความเร่งด่วน — น้อย = ขึ้นบน (เลยกำหนดติดลบ อยู่บนสุด) ตาม prototype */
function urgency(r) {
  if (r.type === "daily") return 1;
  if (r.type === "as_needed") {
    if (r.threshold == null) return 99;
    return r.due ? 0 : 1 + (r.threshold - r.uses_count);
  }
  const remain = r.days_until_due;
  if (remain == null) return 0; // ยังไม่เคยทำ = ถึงรอบทันที
  return remain <= 0 ? remain : 1 + remain;
}

function Badge({ r }) {
  if (r.done_today)
    return <span className="rounded-full bg-surface2 px-2.5 py-1 text-[11px] text-faint">✓ ทำแล้ว</span>;
  if (r.due)
    return <span className="rounded-full bg-red/15 px-2.5 py-1 text-[11px] font-semibold text-red">ถึงรอบแล้ว</span>;
  const text =
    r.type === "as_needed"
      ? `อีก ${r.threshold - r.uses_count} ครั้ง`
      : remainLabel(r.days_until_due);
  return <span className="rounded-full bg-surface2 px-2.5 py-1 text-[11px] text-faint">{text}</span>;
}

function CheckinButton({ r, label, onToggle }) {
  return (
    <button
      onClick={() => onToggle(r)}
      className={`w-full rounded-xl py-3 text-[13px] ${
        r.done_today
          ? "border border-green bg-green/15 text-green"
          : "border border-dashed border-line bg-surface2 text-dim"
      }`}
    >
      {r.done_today ? (
        <>
          ✓ {label}แล้ว
          <small className="mt-0.5 block text-[10px] text-dim">แตะอีกครั้งเพื่อยกเลิก</small>
        </>
      ) : (
        label
      )}
    </button>
  );
}

function CardHead({ r, right, onActions }) {
  return (
    <div className="mb-3 flex items-center gap-2">
      <span className="min-w-0 flex-1 truncate text-sm font-semibold">{r.name}</span>
      {right}
      <button className="shrink-0 pl-2 text-sm text-faint" onClick={() => onActions(r)}>
        ⋯
      </button>
    </div>
  );
}

/* daily: streak 🔥 + จุด 7 วัน (index 6 = วันนี้) */
function DailyCard({ r, onToggle, onActions }) {
  const today = new Date();
  return (
    <div className="mb-2.5 rounded-2xl border border-line bg-surface p-4">
      <CardHead
        r={r}
        onActions={onActions}
        right={<span className="shrink-0 text-xs text-yellow">🔥 {r.streak}</span>}
      />
      <div className="mb-3 flex justify-between gap-1.5">
        {r.last_7_days.map((hit, i) => {
          const day = new Date(today);
          day.setDate(today.getDate() - (6 - i));
          return (
            <div
              key={i}
              className={`flex size-9 items-center justify-center rounded-full border text-[10px] ${
                hit ? "border-green bg-green/15 text-green" : "border-line bg-surface2 text-faint"
              }`}
            >
              {DAY_NAMES[day.getDay()]}
            </div>
          );
        })}
      </div>
      <CheckinButton r={r} label="เช็คอินวันนี้" onToggle={onToggle} />
    </div>
  );
}

/* interval + as_needed: ทำล่าสุด + badge; as_needed มีแถบนับ uses */
function CycleCard({ r, onToggle, onAddUse, onRemoveUse, onActions }) {
  const showUses = r.type === "as_needed" && !r.done_today;
  const pct = showUses ? Math.min(100, Math.round((r.uses_count / r.threshold) * 100)) : 0;

  return (
    <div className="mb-2.5 rounded-2xl border border-line bg-surface p-4">
      <CardHead
        r={r}
        onActions={onActions}
        right={
          <span className="shrink-0 rounded-full bg-surface2 px-2 py-0.5 text-[10px] text-faint">
            {freqLabel(r)}
          </span>
        }
      />
      <div className="mb-3 flex items-center justify-between text-xs text-dim">
        <span>ทำล่าสุด: {lastDoneLabel(r)}</span>
        <Badge r={r} />
      </div>

      {showUses ? (
        <>
          <div className="mb-3 flex items-center gap-2.5">
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-surface2">
              <div
                className={`h-full rounded-full transition-all ${r.due ? "bg-red" : "bg-accent"}`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="min-w-11 shrink-0 text-right text-xs text-dim">
              {r.uses_count}/{r.threshold}
            </span>
          </div>
          <div className="flex gap-2">
            {r.uses_count > 0 && (
              <button
                onClick={() => onRemoveUse(r)}
                className="w-13 shrink-0 rounded-xl border border-line bg-surface2 py-3 text-[13px] text-dim"
                title="กดพลาด ลบ 1"
              >
                −1
              </button>
            )}
            {r.due ? (
              /* ครบ threshold: ปุ่ม ＋ ถูกแทนที่ด้วยปุ่มแดง "ทำแล้ววันนี้" */
              <button
                onClick={() => onToggle(r)}
                className="flex-1 animate-popin rounded-xl border border-red bg-red/15 py-3 text-[13px] text-red"
              >
                ทำแล้ววันนี้
              </button>
            ) : (
              <button
                onClick={() => onAddUse(r)}
                className="flex-1 rounded-xl border border-accent bg-accent/15 py-3 text-[13px] font-semibold text-accent"
              >
                ＋ ใช้แล้ว 1 ครั้ง
              </button>
            )}
          </div>
        </>
      ) : (
        <CheckinButton r={r} label="ทำแล้ววันนี้" onToggle={onToggle} />
      )}
    </div>
  );
}

/* เสร็จแล้ววันนี้ยุบเป็นแถวเล็กจาง + ยกเลิกได้ */
function DoneRow({ r, onToggle }) {
  return (
    <div className="mb-1.5 flex items-center gap-2.5 rounded-xl border border-line bg-surface px-3.5 py-2.5 text-[13px] text-dim opacity-65">
      <span className="text-green">✓</span>
      <span className="min-w-0 flex-1 truncate">{r.name}</span>
      {r.type === "daily" ? (
        <span className="shrink-0 text-xs text-yellow">🔥 {r.streak}</span>
      ) : (
        <span className="shrink-0 rounded-full bg-surface2 px-2 py-0.5 text-[10px] text-faint">
          {freqLabel(r)}
        </span>
      )}
      <button className="shrink-0 p-1 text-xs text-faint" onClick={() => onToggle(r)}>
        ยกเลิก
      </button>
    </div>
  );
}

function Empty({ children }) {
  return <div className="py-8 text-center text-[13px] text-faint">{children}</div>;
}

export default function RoutinePage() {
  const [routines, setRoutines] = useState([]);
  const [tab, setTab] = useState("today");
  const [error, setError] = useState("");

  const [sheetOpen, setSheetOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [actionRoutine, setActionRoutine] = useState(null);

  async function load() {
    try {
      setRoutines(await api.listRoutines());
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  // checkin/uses ได้ routine ที่อัปเดตกลับมา — แทนที่ในลิสต์เลย ไม่ต้องโหลดใหม่
  function replace(updated) {
    setRoutines((rs) => rs.map((r) => (r.id === updated.id ? updated : r)));
  }

  async function toggleCheckin(r) {
    try {
      replace(r.done_today ? await api.cancelCheckin(r.id) : await api.checkinRoutine(r.id));
    } catch (err) {
      setError(err.message);
    }
  }
  const addUse = async (r) => replace(await api.addRoutineUse(r.id));
  const removeUse = async (r) => replace(await api.removeRoutineUse(r.id));

  async function saveRoutine(data) {
    if (editing) await api.updateRoutine(editing.id, data);
    else await api.createRoutine(data);
    setSheetOpen(false);
    setEditing(null);
    await load();
  }

  async function deleteFromActions() {
    const r = actionRoutine;
    setActionRoutine(null);
    if (!window.confirm(`ลบ "${r.name}"?`)) return;
    await api.deleteRoutine(r.id);
    await load();
  }

  const cardProps = {
    onToggle: toggleCheckin,
    onAddUse: addUse,
    onRemoveUse: removeUse,
    onActions: setActionRoutine,
  };
  const card = (r) =>
    r.type === "daily" ? (
      <DailyCard key={r.id} r={r} {...cardProps} />
    ) : (
      <CycleCard key={r.id} r={r} {...cardProps} />
    );
  const byUrgency = (a, b) => urgency(a) - urgency(b);

  let content;
  if (tab === "daily") {
    // habit รายวันทั้งหมด (การ์ดเต็ม เห็น streak + จุด 7 วัน)
    const list = routines.filter((r) => r.type === "daily");
    content = list.length ? list.map(card) : <Empty>ยังไม่มี habit รายวัน</Empty>;
  } else if (tab === "cycle") {
    // งานเป็นรอบ + ตามสภาพ เรียงตามใกล้ถึงรอบ
    const list = routines.filter((r) => r.type !== "daily").sort(byUrgency);
    content = list.length ? list.map(card) : <Empty>ยังไม่มีงานเป็นรอบ</Empty>;
  } else {
    // วันนี้: รายวันที่ยังไม่ทำ + ที่ถึงรอบ เรียงตามเร่งด่วน / ทำแล้วย่อส่วน
    const active = routines
      .filter((r) => !r.done_today && (r.type === "daily" || r.due))
      .sort(byUrgency);
    const done = routines.filter((r) => r.done_today);
    content = (
      <>
        {active.length ? active.map(card) : <Empty>วันนี้ครบหมดแล้ว 🎉</Empty>}
        {done.length > 0 && (
          <>
            <div className="mb-2 mt-4.5 text-xs font-semibold uppercase tracking-wide text-faint">
              เสร็จแล้ววันนี้ · {done.length}
            </div>
            {done.map((r) => (
              <DoneRow key={r.id} r={r} onToggle={toggleCheckin} />
            ))}
          </>
        )}
      </>
    );
  }

  return (
    <>
      <div className="h-full animate-fadein overflow-y-auto px-4 pt-10 pb-44">
        <div className="text-[26px] font-bold">Routine</div>
        <div className="mb-5 mt-0.5 text-[13px] text-dim">habit รายวัน + งานดูแลที่ทำเป็นรอบ</div>
        {error && <p className="mb-4 text-sm text-red">{error}</p>}
        {content}
      </div>

      {/* segmented tab ลอยเหนือ tab bar — โซนนิ้วโป้ง */}
      <div className="absolute bottom-[104px] left-3.5 right-[84px] z-30 flex rounded-full border border-line bg-surface/90 p-1 backdrop-blur-md">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex-1 whitespace-nowrap rounded-full px-3 py-2 text-center text-[13px] ${
              tab === t.key ? "bg-accent/15 text-accent" : "text-dim"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* FAB เพิ่ม routine */}
      <button
        onClick={() => {
          setEditing(null);
          setSheetOpen(true);
        }}
        className="absolute bottom-24 right-4 z-40 flex size-14 items-center justify-center rounded-full bg-accent text-2xl text-white shadow-[0_8px_24px_rgba(99,102,241,.4)]"
      >
        ＋
      </button>

      <RoutineSheet
        open={sheetOpen}
        routine={editing}
        onClose={() => {
          setSheetOpen(false);
          setEditing(null);
        }}
        onSave={saveRoutine}
      />
      <ActionSheet
        open={actionRoutine !== null}
        title={actionRoutine?.name}
        onClose={() => setActionRoutine(null)}
        onEdit={() => {
          const r = actionRoutine;
          setActionRoutine(null);
          setEditing(r);
          setSheetOpen(true);
        }}
        onDelete={deleteFromActions}
      />
    </>
  );
}
