/**
 * Centralized API client with JWT token injection.
 * All backend calls go through this module.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("vidora_token");
}

export function setToken(token: string) {
  localStorage.setItem("vidora_token", token);
}

export function clearToken() {
  localStorage.removeItem("vidora_token");
}

/**
 * Authenticated fetch wrapper. Auto-injects JWT Bearer token.
 * Redirects to /login on 401 responses.
 */
export async function apiFetch(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Don't set Content-Type for FormData (browser sets boundary automatically)
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = headers["Content-Type"] || "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401 && typeof window !== "undefined") {
    clearToken();
    window.location.href = "/login";
  }

  return res;
}

// ── Typed API helpers ──────────────────────────────────────────

export async function loginUser(email: string, password: string) {
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  const res = await fetch(`${API_BASE}/users/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Login failed");
  }

  const data = await res.json();
  setToken(data.access_token);
  return data;
}

export async function registerUser(email: string, password: string) {
  const res = await fetch(`${API_BASE}/users/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Registration failed");
  }

  return res.json();
}

export async function uploadVideo(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await apiFetch("/videos/upload", {
    method: "POST",
    body: formData,
  });

  if (!res.ok) throw new Error("Upload failed");
  return res.json();
}

export async function getVideoStatus(videoId: string) {
  const res = await apiFetch(`/videos/status/${videoId}`);
  if (!res.ok) return null;
  return res.json();
}

export async function getVideoResults(videoId: string) {
  const res = await apiFetch(`/videos/results/${videoId}`);
  if (!res.ok) return null;
  return res.json();
}

export async function getMyVideos() {
  const res = await apiFetch("/videos/my-videos");
  if (!res.ok) return [];
  return res.json();
}

export async function queryVideo(videoId: string, query: string) {
  const res = await apiFetch("/query/", {
    method: "POST",
    body: JSON.stringify({ video_id: videoId, query }),
  });

  if (!res.ok) throw new Error("Query failed");
  return res.json();
}

export function getVideoStreamUrl(videoId: string): string {
  return `${API_BASE}/videos/stream/${videoId}`;
}
