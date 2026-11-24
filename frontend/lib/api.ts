export const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export type HealthResponse = {
  status: string;
  service: string;
  version: string;
  timestamp: string;
};

export type AppSettings = {
  provider: "gemini" | "groq";
  gemini_model: string;
  groq_model: string;
  rag_top_k: number;
  theme: "dark" | "light" | "system";
  provider_configured: boolean;
};

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_URL}/api/health`, { cache: "no-store" });
  if (!response.ok) throw new Error("Backend is unavailable");
  return response.json();
}

export async function fetchSettings(): Promise<AppSettings> {
  const response = await fetch(`${API_URL}/api/settings`, { cache: "no-store" });
  if (!response.ok) throw new Error("Could not load settings");
  return response.json();
}

