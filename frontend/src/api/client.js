const BASE = "/api/v1";

function getToken() {
  return localStorage.getItem("lift_token");
}

export function setToken(token) {
  if (token) localStorage.setItem("lift_token", token);
  else localStorage.removeItem("lift_token");
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (res.status === 204) return null;
  const body = await res.json().catch(() => null);

  if (!res.ok) {
    const message = body?.detail || `Request failed (${res.status})`;
    const error = new Error(typeof message === "string" ? message : "Request failed");
    error.status = res.status;
    throw error;
  }
  return body;
}

// --- auth ---
export const api = {
  register: (data) => request("/auth/register", { method: "POST", body: JSON.stringify(data) }),
  login: (data) => request("/auth/login", { method: "POST", body: JSON.stringify(data) }),
  me: () => request("/auth/me"),

  // --- tasks ---
  listTasks: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/tasks${qs ? `?${qs}` : ""}`);
  },
  createTask: (data) => request("/tasks", { method: "POST", body: JSON.stringify(data) }),
  updateTask: (id, data) => request(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteTask: (id) => request(`/tasks/${id}`, { method: "DELETE" }),

  // --- dashboard ---
  getDashboard: () => request("/dashboard"),

  // --- routines ---
  listRoutines: () => request("/routines"),
  createRoutine: (data) => request("/routines", { method: "POST", body: JSON.stringify(data) }),
  updateRoutine: (id, data) => request(`/routines/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteRoutine: (id) => request(`/routines/${id}`, { method: "DELETE" }),
  checkinRoutine: (id) => request(`/routines/${id}/checkin`, { method: "POST", body: JSON.stringify({}) }),
  cancelCheckin: (id) => request(`/routines/${id}/checkin`, { method: "DELETE" }),
  addRoutineUse: (id) => request(`/routines/${id}/uses`, { method: "POST" }),
  removeRoutineUse: (id) => request(`/routines/${id}/uses`, { method: "DELETE" }),

  // --- journal ---
  listJournal: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/journal${qs ? `?${qs}` : ""}`);
  },
  upsertJournal: (data) => request("/journal", { method: "POST", body: JSON.stringify(data) }),
  deleteJournal: (id) => request(`/journal/${id}`, { method: "DELETE" }),

  // --- categories ---
  listCategories: () => request("/categories"),
  createCategory: (data) => request("/categories", { method: "POST", body: JSON.stringify(data) }),
  updateCategory: (id, data) => request(`/categories/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteCategory: (id) => request(`/categories/${id}`, { method: "DELETE" }),
};
