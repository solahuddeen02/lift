import BottomSheet from "./BottomSheet.jsx";

/* action sheet แก้ไข/ลบ — เด้งจากล่างแทนปุ่มบนการ์ด กดถึงด้วยนิ้วโป้ง */
export default function ActionSheet({ open, title, onClose, onEdit, onDelete }) {
  return (
    <BottomSheet open={open} onClose={onClose} title={title}>
      <button
        onClick={onEdit}
        className="w-full rounded-xl bg-accent py-3.5 text-[15px] font-semibold text-white"
      >
        ✎ แก้ไข
      </button>
      <button
        onClick={onDelete}
        className="mt-2.5 w-full rounded-xl bg-red/15 py-3.5 text-[15px] font-semibold text-red"
      >
        ✕ ลบ
      </button>
    </BottomSheet>
  );
}
