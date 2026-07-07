import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import ActionSheet from "../components/ActionSheet.jsx";
import CategorySheet from "../components/CategorySheet.jsx";
import TaskSheet from "../components/TaskSheet.jsx";

const GROUPS = ["เลยกำหนด", "วันนี้", "พรุ่งนี้", "ถัดไป", "ไม่มีกำหนด"];
const PRIO_ORDER = { high: 0, medium: 1, low: 2 };
const PRIO_STYLES = {
  high: "bg-red/15 text-red",
  medium: "bg-yellow/15 text-yellow",
  low: "bg-surface2 text-dim",
};
const FILTERS = [
  { key: "all", label: "ทั้งหมด" },
  { key: "todo", label: "ค้างอยู่" },
  { key: "done", label: "เสร็จแล้ว" },
];

function dayDiff(dueDate) {
  const d0 = new Date();
  d0.setHours(0, 0, 0, 0);
  const d1 = new Date(dueDate);
  d1.setHours(0, 0, 0, 0);
  return Math.round((d1 - d0) / 864e5);
}

function taskGroup(t) {
  if (!t.due_date) return "ไม่มีกำหนด";
  const diff = dayDiff(t.due_date);
  if (diff < 0) return "เลยกำหนด";
  if (diff === 0) return "วันนี้";
  if (diff === 1) return "พรุ่งนี้";
  return "ถัดไป";
}

function DueLabel({ task }) {
  if (!task.due_date) return null;
  const diff = dayDiff(task.due_date);
  const done = task.status === "done";
  if (diff < 0 && !done) return <span className="text-[11px] text-red">เลยกำหนด</span>;
  const text =
    diff === 0
      ? "วันนี้"
      : diff === 1
        ? "พรุ่งนี้"
        : new Date(task.due_date).toLocaleDateString("th-TH", { day: "numeric", month: "short" });
  return <span className="text-[11px] text-dim">{text}</span>;
}

function CatTag({ cat }) {
  if (!cat) return null;
  return (
    <span
      className="shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold"
      style={{ background: `${cat.color}26`, color: cat.color }}
    >
      {cat.name}
    </span>
  );
}

function TaskRow({ task, cat, onToggle, onEdit, onActions }) {
  return (
    <div className="mb-2 flex items-center gap-3 rounded-2xl border border-line bg-surface p-3.5">
      <input
        type="checkbox"
        checked={false}
        onChange={() => onToggle(task)}
        className="size-5 shrink-0 accent-accent"
      />
      <div className="min-w-0 flex-1 cursor-pointer" onClick={() => onEdit(task)}>
        <div className="truncate text-sm">{task.title}</div>
        <div className="mt-1 flex items-center gap-2">
          <span
            className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold ${PRIO_STYLES[task.priority]}`}
          >
            {task.priority}
          </span>
          <CatTag cat={cat} />
          <DueLabel task={task} />
          {task.note && (
            <span className="max-w-[170px] truncate text-[11px] text-dim">📝 {task.note}</span>
          )}
        </div>
      </div>
      <button className="shrink-0 px-1 text-faint" onClick={() => onActions(task)}>
        ⋯
      </button>
    </div>
  );
}

/* เสร็จแล้วยุบเป็นแถวเล็กจาง + ปุ่มยกเลิก (กันกดพลาด) */
function DoneRow({ task, cat, onToggle }) {
  return (
    <div className="mb-1.5 flex items-center gap-2.5 rounded-xl border border-line bg-surface px-3.5 py-2.5 text-[13px] text-dim opacity-65">
      <span className="text-green">✓</span>
      <span className="min-w-0 flex-1 truncate line-through">{task.title}</span>
      <CatTag cat={cat} />
      <button className="shrink-0 p-1 text-xs text-faint" onClick={() => onToggle(task)}>
        ยกเลิก
      </button>
    </div>
  );
}

export default function TasksPage() {
  const { logout } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [categories, setCategories] = useState([]);
  const [filter, setFilter] = useState("all");
  const [catFilter, setCatFilter] = useState(null);
  const [error, setError] = useState("");

  // sheets
  const [taskSheetOpen, setTaskSheetOpen] = useState(false);
  const [editing, setEditing] = useState(null); // task ที่กำลังแก้ (null = เพิ่มใหม่)
  const [catSheetOpen, setCatSheetOpen] = useState(false);
  const [actionTask, setActionTask] = useState(null);

  async function load() {
    try {
      const [t, c] = await Promise.all([api.listTasks(), api.listCategories()]);
      setTasks(t);
      setCategories(c);
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const catMap = useMemo(
    () => Object.fromEntries(categories.map((c) => [c.id, c])),
    [categories]
  );
  const activeCat = catFilter != null ? catMap[catFilter] : null;

  const visible = activeCat ? tasks.filter((t) => t.category_id === catFilter) : tasks;
  const pending = visible.filter((t) => t.status !== "done");
  const done = visible.filter((t) => t.status === "done");

  async function saveTask(data) {
    if (editing) await api.updateTask(editing.id, data);
    else await api.createTask(data);
    setTaskSheetOpen(false);
    setEditing(null);
    await load();
  }

  async function toggleTask(task) {
    await api.updateTask(task.id, { status: task.status === "done" ? "todo" : "done" });
    await load();
  }

  function openEdit(task) {
    setEditing(task);
    setTaskSheetOpen(true);
  }

  async function deleteFromActions() {
    const task = actionTask;
    setActionTask(null);
    if (!window.confirm(`ลบ "${task.title}"?`)) return;
    await api.deleteTask(task.id);
    await load();
  }

  const rowProps = { onToggle: toggleTask, onEdit: openEdit, onActions: setActionTask };

  return (
    <>
      <div className="h-full animate-fadein overflow-y-auto px-4 pt-10 pb-44">
        <div className="flex items-start justify-between">
          <div className="text-[26px] font-bold">Tasks</div>
          <button onClick={logout} className="mt-2 text-xs text-faint">
            ออกจากระบบ
          </button>
        </div>
        <div className="mb-5 mt-0.5 text-[13px] text-dim">ค้างอยู่ {pending.length} งาน</div>

        {error && <p className="mb-4 text-sm text-red">{error}</p>}

        {/* จัดกลุ่มตามเวลา → ในกลุ่มเรียง priority สูง→ต่ำ */}
        {filter !== "done" &&
          GROUPS.map((g) => {
            const list = pending
              .filter((t) => taskGroup(t) === g)
              .sort((a, b) => PRIO_ORDER[a.priority] - PRIO_ORDER[b.priority]);
            if (!list.length) return null;
            return (
              <div key={g}>
                <div
                  className={`mb-2 mt-4.5 text-xs font-semibold uppercase tracking-wide first:mt-0 ${
                    g === "เลยกำหนด" ? "text-red" : "text-faint"
                  }`}
                >
                  {g} · {list.length}
                </div>
                {list.map((t) => (
                  <TaskRow key={t.id} task={t} cat={catMap[t.category_id]} {...rowProps} />
                ))}
              </div>
            );
          })}
        {filter !== "done" && !pending.length && !error && (
          <div className="py-8 text-center text-[13px] text-faint">ไม่มี task ค้าง 🎉</div>
        )}

        {filter !== "todo" && done.length > 0 && (
          <>
            <div className="mb-2 mt-4.5 text-xs font-semibold uppercase tracking-wide text-faint">
              เสร็จแล้ว · {done.length}
            </div>
            {done.map((t) => (
              <DoneRow key={t.id} task={t} cat={catMap[t.category_id]} onToggle={toggleTask} />
            ))}
          </>
        )}
      </div>

      {/* filter pills ลอยเหนือ tab bar — โซนนิ้วโป้ง */}
      <div className="absolute bottom-[104px] left-3.5 right-[84px] z-30 flex overflow-x-auto rounded-full border border-line bg-surface/90 p-1 backdrop-blur-md">
        <button
          onClick={() => setCatSheetOpen(true)}
          className={`flex shrink-0 items-center gap-1.5 rounded-l-full border-r border-line px-3.5 py-2 text-[13px] ${
            activeCat ? "bg-accent/15 text-accent" : "text-dim"
          }`}
        >
          {activeCat ? (
            <>
              <span className="size-2.5 rounded-full" style={{ background: activeCat.color }} />
              {activeCat.name}
            </>
          ) : (
            "🏷"
          )}
        </button>
        {FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`flex-1 whitespace-nowrap rounded-full px-3 py-2 text-center text-[13px] ${
              filter === f.key ? "bg-accent/15 text-accent" : "text-dim"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* FAB เพิ่ม task */}
      <button
        onClick={() => {
          setEditing(null);
          setTaskSheetOpen(true);
        }}
        className="absolute bottom-24 right-4 z-40 flex size-14 items-center justify-center rounded-full bg-accent text-2xl text-white shadow-[0_8px_24px_rgba(99,102,241,.4)]"
      >
        ＋
      </button>

      <TaskSheet
        open={taskSheetOpen}
        task={editing}
        categories={categories}
        onClose={() => {
          setTaskSheetOpen(false);
          setEditing(null);
        }}
        onSave={saveTask}
      />
      <CategorySheet
        open={catSheetOpen}
        categories={categories}
        value={catFilter}
        onSelect={(id) => {
          setCatFilter(id);
          setCatSheetOpen(false);
        }}
        onClose={() => setCatSheetOpen(false)}
      />
      <ActionSheet
        open={actionTask !== null}
        title={actionTask?.title}
        onClose={() => setActionTask(null)}
        onEdit={() => {
          const t = actionTask;
          setActionTask(null);
          openEdit(t);
        }}
        onDelete={deleteFromActions}
      />
    </>
  );
}
