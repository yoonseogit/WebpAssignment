const API_BASE = import.meta.env.VITE_API_BASE || "";

export function getStoredAuth() {
  const raw = localStorage.getItem("coinsight:auth");
  return raw ? JSON.parse(raw) : null;
}

export function setStoredAuth(auth) {
  localStorage.setItem("coinsight:auth", JSON.stringify(auth));
}

export function clearStoredAuth() {
  localStorage.removeItem("coinsight:auth");
}

export async function request(path, options = {}) {
  const auth = getStoredAuth();
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (auth?.access_token) {
    headers.Authorization = `Bearer ${auth.access_token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "요청을 처리하지 못했습니다.");
  }
  return data;
}
