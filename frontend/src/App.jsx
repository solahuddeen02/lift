import { useState } from "react";
import { useAuth } from "./context/AuthContext.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import TasksPage from "./pages/TasksPage.jsx";
import RoutinePage from "./pages/RoutinePage.jsx";
import JournalPage from "./pages/JournalPage.jsx";
import TabBar from "./components/TabBar.jsx";

const PAGES = {
  dashboard: DashboardPage,
  tasks: TasksPage,
  habits: RoutinePage,
  journal: JournalPage,
};

export default function App() {
  const { user, loading } = useAuth();
  const [tab, setTab] = useState("dashboard"); // เปิดแอพมาเจอหน้าหลักตาม prototype

  if (loading) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-bg text-dim">Loading…</div>
    );
  }
  if (!user) return <LoginPage />;

  const Page = PAGES[tab];

  return (
    // กรอบแอพ mobile-first: relative เพื่อให้ FAB / filter ลอย / sheet ยึดกับกรอบนี้
    <div className="relative mx-auto h-dvh max-w-md overflow-hidden bg-bg text-ink">
      <Page key={tab} onNavigate={setTab} />
      <TabBar tab={tab} onChange={setTab} />
    </div>
  );
}
