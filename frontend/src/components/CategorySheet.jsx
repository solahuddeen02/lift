import BottomSheet from "./BottomSheet.jsx";

/* sheet เลือกหมวดกรอง — ปุ่มแถวใหญ่ กดง่ายมือเดียว (value=null คือทุกหมวด) */
export default function CategorySheet({ open, categories, value, onSelect, onClose }) {
  const options = [{ id: null, name: "ทุกหมวด", color: null }, ...categories];
  return (
    <BottomSheet open={open} onClose={onClose} title="กรองตามหมวด">
      {options.map((c) => (
        <button
          key={c.id ?? "all"}
          onClick={() => onSelect(c.id)}
          className={`mb-2 flex w-full items-center gap-3 rounded-xl border px-3.5 py-3.5 text-left text-sm text-ink ${
            value === c.id ? "border-accent bg-accent/15" : "border-line bg-surface2"
          }`}
        >
          <span
            className="size-2.5 shrink-0 rounded-full"
            style={{ background: c.color || "var(--color-faint)" }}
          />
          {c.name}
          {value === c.id && <span className="ml-auto text-accent">✓</span>}
        </button>
      ))}
    </BottomSheet>
  );
}
