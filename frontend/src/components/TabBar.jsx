const TABS = [
  { key: "dashboard", icon: "◧", label: "หน้าหลัก" },
  { key: "tasks", icon: "☑", label: "Tasks" },
  { key: "habits", icon: "↻", label: "Routine" },
  { key: "journal", icon: "✎", label: "Journal" },
];

export default function TabBar({ tab, onChange }) {
  return (
    <nav className="absolute inset-x-0 bottom-0 z-40 flex border-t border-line bg-surface/90 px-2 pt-2.5 pb-6 backdrop-blur-md">
      {TABS.map((t) => (
        <button
          key={t.key}
          onClick={() => onChange(t.key)}
          className={`flex flex-1 flex-col items-center gap-1 text-[10px] transition ${
            tab === t.key ? "text-accent" : "text-faint"
          }`}
        >
          <span className="text-xl leading-none">{t.icon}</span>
          {t.label}
        </button>
      ))}
    </nav>
  );
}
