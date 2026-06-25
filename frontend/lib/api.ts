/**
 * AVA API Client — axios with auto auth headers
 */

import axios from "axios";
import { getSession } from "next-auth/react";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  timeout: 30000,
});

// Auto-attach JWT from NextAuth session
api.interceptors.request.use(async (config) => {
  const session = await getSession();
  if (session && (session as any).accessToken) {
    config.headers.Authorization = `Bearer ${(session as any).accessToken}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      // Redirect to login — handled by NextAuth
      if (typeof window !== "undefined") window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default api;

// ── Auth helpers ─────────────────────────────────────────────────
export const authApi = {
  signup: (name: string, email: string, password: string) =>
    api.post("/api/auth/signup", { name, email, password }),
  me: () => api.get("/api/auth/me"),
};

// ── Chat helpers ─────────────────────────────────────────────────
export const chatApi = {
  createSession: (title?: string) =>
    api.post("/api/chat/sessions", { title }),
  getSessions: () => api.get("/api/chat/sessions"),
  getSession: (id: string) => api.get(`/api/chat/sessions/${id}`),
  deleteSession: (id: string) => api.delete(`/api/chat/sessions/${id}`),
  sendMessage: (sessionId: string, content: string) =>
    api.post(`/api/chat/sessions/${sessionId}/messages`, { content }),
};

// ── Voice helpers ─────────────────────────────────────────────────
export const voiceApi = {
  transcribe: (audioBlob: Blob) => {
    const form = new FormData();
    form.append("audio", audioBlob, "recording.webm");
    return api.post("/api/voice/transcribe", form);
  },
  speak: (text: string) =>
    api.post("/api/voice/speak", { text }, { responseType: "blob" }),
};
