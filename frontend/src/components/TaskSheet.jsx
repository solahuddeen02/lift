import { useEffect, useState } from "react";
import BottomSheet from "./BottomSheet.jsx";

const inputCls =
  "w-full rounded-xl border border-line bg-surface2 px-3.5 py-3 text-sm text-ink outline-none [color-scheme:dark] placeholder:text-faint focus:border-accent";

/* sheet เพิ่ม/แก้ไข task — task=null คือเพิ่มใหม่ */
export default function TaskSheet({ open, task, categories, onClose, onSave }) {
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState("medium");
  const [due, setDue] = useState("");
  const [categoryId, setCategoryId] = useState(null);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!open) return;
    setTitle(task?.title ?? "");
    setPriority(task?.priority ?? "medium");
    setDue(task?.due_date ? task.due_date.slice(0, 10) : "");
    setCategoryId(task?.category_id ?? null);
    setNote(task?.note ?? "");
  }, [open, task]);

  async function submit() {
    if (!title.trim() || busy) return;
    setBusy(true);
    try {
      await onSave({
        title: title.trim(),
        priority,
        due_date: due ? new Date(due).toISOString() : null,
        category_id: categoryId,
        note: note.trim(),
      });
    } finally {
      setBusy(false);
    }
  }

  return (
    <BottomSheet open={open} onClose={onClose} title={task ? "แก้ไข Task" : "เพิ่ม Task ใหม่"}>
      <input
        type="text"
        placeholder="ชื่อ task…"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && submit()}
        autoFocus
        className={`${inputCls} mb-2.5`}
      />
      <div className="mb-2.5 flex gap-2.5">
        <select value={priority} onChange={(e) => setPriority(e.target.value)} className={inputCls}>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
        <input type="date" value={due} onChange={(e) => setDue(e.target.value)} className={inputCls} />
      </div>
      <div className="mb-2.5 flex flex-wrap gap-1.5">
        {[{ id: null, name: "ไม่ระบุ" }, ...categories].map((c) => (
          <button
            key={c.id ?? "none"}
            type="button"
            onClick={() => setCategoryId(c.id)}
            className={`rounded-full border px-3 py-1.5 text-xs ${
              categoryId === c.id
                ? "border-accent bg-accent/15 text-accent"
                : "border-line bg-surface text-dim"
            }`}
          >
            {c.name}
          </button>
        ))}
      </div>
      <textarea
        placeholder="โน้ต / รายละเอียด (ไม่บังคับ)"
        value={note}
        onChange={(e) => setNote(e.target.value)}
        className={`${inputCls} mb-2.5 min-h-[70px] resize-none leading-relaxed`}
      />
      <button
        onClick={submit}
        disabled={busy || !title.trim()}
        className="w-full rounded-xl bg-accent py-3.5 text-[15px] font-semibold text-white disabled:opacity-50"
      >
        {task ? "บันทึก" : "เพิ่ม"}
      </button>
    </BottomSheet>
  );
}
