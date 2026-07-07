/* bottom sheet มาตรฐานตาม prototype — ทุก interaction เด้งจากล่าง โซนนิ้วโป้ง */
export default function BottomSheet({ open, onClose, title, children }) {
  if (!open) return null;
  return (
    <div
      className="absolute inset-0 z-50 bg-black/55"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="absolute inset-x-0 bottom-0 animate-slideup rounded-t-3xl bg-surface px-5 pt-5 pb-9">
        <div className="mx-auto mb-4 h-1 w-10 rounded-full bg-line" />
        {title && <h3 className="mb-3.5 font-semibold">{title}</h3>}
        {children}
      </div>
    </div>
  );
}
