import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import TaskSheet from "../components/TaskSheet.jsx";

const DAY_NAMES = ["อา", "จ", "อ", "พ", "พฤ", "ศ", "ส"];
const PRIO_COLORS = {
  high: "var(--color-red)",
  medium: "var(--color-yellow)",
  low: "var(--color-faint)",
};

function greeting() {
  const hour = new Date().getHours();
  return hour < 12 ? "สวัสดีตอนเช้า" : hour < 18 ? "สวัสดีตอนบ่าย" : "สวัสดีตอนค่ำ";
}

function dayDiff(dateStr) {
  const d0 = new Date();
  d0.setHours(0, 0, 0, 0);
  const d1 = new Date(dateStr);
  d1.setHours(0, 0, 0, 0);
  return Math.round((d1 - d0) / 864e5);
}

function dueLabel(t) {
  if (!t.due_date) return null;
  const diff = dayDiff(t.due_date);
  if (diff < 0) return { text: "เลยกำหนด", overdue: true };
  if (diff === 0) return { text: "วันนี้" };
  if (diff === 1) return { text: "พรุ่งนี้" };
  return {
    text: new Date(t.due_date).toLocaleDateString("th-TH", { day: "numeric", month: "short" }),
  };
}

function journalDateLabel(iso) {
  const diff = -dayDiff(iso);
  if (diff <= 0) return "วันนี้";
  if (diff === 1) return "เมื่อวาน";
  if (diff < 7) return `${diff} วันก่อน`;
  return new Date(iso).toLocaleDateString("th-TH", { day: "numeric", month: "short" });
}

/* วงแหวน progress ตาม prototype */
function Ring({ pct, color }) {
  const r = 21;
  const c = 2 * Math.PI * r;
  return (
    <svg width="52" height="52" viewBox="0 0 52 52" className="shrink-0">
      <circle cx="26" cy="26" r={r} fill="none" stroke="var(--color-surface2)" strokeWidth="6" />
      <circle
        cx="26"
        cy="26"
        r={r}
        fill="none"
        stroke={color}
        strokeWidth="6"
        strokeDasharray={c}
        strokeDashoffset={c * (1 - pct)}
        strokeLinecap="round"
        transform="rotate(-90 26 26)"
      />
      <text
        x="26"
        y="30"
        textAnchor="middle"
        fontSize="12"
        fontWeight="700"
        fill="var(--color-ink)"
      >
        {Math.round(pct * 100)}%
      </text>
    </svg>
  );
}

function Card({ className = "", onClick, children }) {
  return (
    <div
      onClick={onClick}
      className={`rounded-2xl border border-line bg-surface p-4 ${
        onClick ? "cursor-pointer transition active:scale-[.97] active:opacity-85" : ""
      } ${className}`}
    >
      {children}
    </div>
  );
}

export default function DashboardPage({ onNavigate }) {
  const { user, logout } = useAuth();
  const [data, setData] = useState(null);
  const [categories, setCategories] = useState([]);
  const [editing, setEditing] = useState(null);
  const [error, setError] = useState("");

  async function load() {
    try {
      const [d, c] = await Promise.all([api.getDashboard(), api.listCategories()]);
      setData(d);
      setCategories(c);
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function toggleTask(t) {
    await api.updateTask(t.id, { status: "done" });
    await load();
  }

  async function saveTask(payload) {
    await api.updateTask(editing.id, payload);
    setEditing(null);
    await load();
  }

  async function toggleRoutine(r) {
    if (r.done_today) await api.cancelCheckin(r.id);
    else await api.checkinRoutine(r.id);
    await load();
  }

  if (!data) {
    return (
      <div className="flex h-full items-center justify-center text-dim">
        {error || "Loading…"}
      </div>
    );
  }

  const { routines_today: rt, tasks, week, best_streak: streak, latest_journal: journal } = data;
  const routinePct = rt.total ? rt.done / rt.total : 0;
  const taskPct = tasks.total ? tasks.done / tasks.total : 0;

  return (
    <>
      <div className="h-full animate-fadein overflow-y-auto px-4 pt-10 pb-44">
        <div className="flex items-start justify-between">
          <div className="text-[26px] font-bold">
            {greeting()} {user?.display_name || ""} 👋
          </div>
          <button onClick={logout} className="mt-2 shrink-0 text-xs text-faint">
            ออกจากระบบ
          </button>
        </div>
        <div className="mb-5 mt-0.5 text-[13px] text-dim">
          {new Date().toLocaleDateString("th-TH", { weekday: "long", day: "numeric", month: "long" })}
        </div>

        {error && <p className="mb-4 text-sm text-red">{error}</p>}

        {/* วงแหวน progress 2 อัน — กดไปหน้านั้นๆ */}
        <div className="mb-3.5 flex gap-2.5">
          <Card className="flex flex-1 items-center gap-2.5 !p-3" onClick={() => onNavigate("habits")}>
            <Ring pct={routinePct} color="var(--color-green)" />
            <div>
              <div className="text-[11px] text-dim">Routine วันนี้</div>
              <div className="text-[22px] font-bold">
                {rt.done}
                <small className="text-xs font-normal text-dim">/{rt.total}</small>
              </div>
            </div>
          </Card>
          <Card className="flex flex-1 items-center gap-2.5 !p-3" onClick={() => onNavigate("tasks")}>
            <Ring pct={taskPct} color="var(--color-accent)" />
            <div>
              <div className="text-[11px] text-dim">Task ค้าง</div>
              <div className="text-[22px] font-bold">{tasks.total - tasks.done}</div>
            </div>
          </Card>
        </div>

        {/* กราฟแท่ง 7 วัน + mood + streak — กดไป Routine */}
        <Card className="mb-3.5" onClick={() => onNavigate("habits")}>
          <div className="flex items-center justify-between">
            <h3 className="text-[13px] font-semibold text-dim">7 วันล่าสุด</h3>
            <span className="text-xs text-yellow">🔥 {streak} วันติด</span>
          </div>
          <div className="mt-2 flex items-end gap-2">
            {week.map((w, i) => {
              const isToday = i === 6;
              const pct = w.total ? Math.round((w.done / w.total) * 100) : 0;
              return (
                <div key={w.date} className="flex flex-1 flex-col items-center gap-1">
                  <span className="text-[13px] leading-none">{w.mood ?? "·"}</span>
                  <div className="relative h-13 w-full overflow-hidden rounded-lg bg-surface2">
                    <div
                      className={`absolute inset-x-0 bottom-0 rounded-lg transition-all ${
                        isToday ? "bg-green" : "bg-accent"
                      }`}
                      style={{ height: `${pct}%` }}
                    />
                  </div>
                  <span
                    className={`text-[9px] ${isToday ? "font-bold text-green" : "text-faint"}`}
                  >
                    {isToday ? "วันนี้" : DAY_NAMES[new Date(w.date).getDay()]}
                  </span>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Task ที่ต้องทำ: ติ๊กเสร็จได้เลย / แตะชื่อเปิดแก้ไข */}
        <Card className="mb-3.5">
          <h3 className="mb-2 text-[13px] font-semibold text-dim">Task ที่ต้องทำ</h3>
          {tasks.top.length ? (
            tasks.top.map((t) => {
              const due = dueLabel(t);
              return (
                <div
                  key={t.id}
                  className="flex items-center gap-2.5 border-b border-line py-2.5 text-sm last:border-b-0 last:pb-0"
                >
                  <button
                    onClick={() => toggleTask(t)}
                    title="ติ๊กเสร็จ"
                    className="size-5 shrink-0 rounded-full border-[1.5px] active:border-green active:bg-green/15"
                    style={{ borderColor: PRIO_COLORS[t.priority] }}
                  />
                  <span
                    className="min-w-0 flex-1 cursor-pointer truncate"
                    onClick={() => setEditing(t)}
                  >
                    {t.title}
                  </span>
                  {due && (
                    <span className={`shrink-0 text-[11px] ${due.overdue ? "text-red" : "text-dim"}`}>
                      {due.text}
                    </span>
                  )}
                </div>
              );
            })
          ) : (
            <div className="text-[13px] text-faint">ไม่มี task ค้าง 🎉</div>
          )}
          <button className="pt-2.5 text-[13px] text-accent" onClick={() => onNavigate("tasks")}>
            ดูทั้งหมด →
          </button>
        </Card>

        {/* Routine วันนี้: แตะทั้งแถว = เช็คอิน/ยกเลิกจากหน้าหลัก */}
        <Card className="mb-3.5">
          <h3 className="mb-2 text-[13px] font-semibold text-dim">Routine วันนี้</h3>
          {rt.items.length ? (
            rt.items.map((r) => (
              <div
                key={r.id}
                onClick={() => toggleRoutine(r)}
                title="แตะเพื่อเช็คอิน"
                className="flex cursor-pointer items-center gap-2.5 border-b border-line py-2.5 text-sm last:border-b-0 last:pb-0 active:opacity-70"
              >
                <span className={`min-w-0 flex-1 truncate ${r.done_today ? "text-faint" : ""}`}>
                  {r.name}
                </span>
                {r.type !== "daily" && r.due && !r.done_today && (
                  <span className="shrink-0 rounded-full bg-red/15 px-2.5 py-1 text-[11px] font-semibold text-red">
                    ถึงรอบ
                  </span>
                )}
                <span className={r.done_today ? "text-green" : "text-faint"}>
                  {r.done_today ? "✓" : "○"}
                </span>
              </div>
            ))
          ) : (
            <div className="text-[13px] text-faint">ยังไม่มี routine — เพิ่มได้ที่แท็บ Routine</div>
          )}
          <button className="pt-2.5 text-[13px] text-accent" onClick={() => onNavigate("habits")}>
            เช็คอิน →
          </button>
        </Card>

        {/* Journal ล่าสุด — แตะไปหน้า Journal */}
        <Card className="mb-3.5" onClick={() => onNavigate("journal")}>
          <h3 className="mb-2 text-[13px] font-semibold text-dim">Journal ล่าสุด</h3>
          {journal ? (
            <>
              <div className="mb-1 text-xs text-dim">
                {journalDateLabel(journal.entry_date)} · {journal.mood}
              </div>
              <div className="line-clamp-2 text-[13px] leading-relaxed">{journal.text}</div>
            </>
          ) : (
            <div className="text-[13px] text-faint">ยังไม่มีบันทึก</div>
          )}
          <button className="pt-2.5 text-[13px] text-accent">เขียนวันนี้ →</button>
        </Card>
      </div>

      <TaskSheet
        open={editing !== null}
        task={editing}
        categories={categories}
        onClose={() => setEditing(null)}
        onSave={saveTask}
      />
    </>
  );
}
