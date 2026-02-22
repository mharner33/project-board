import type { BoardData } from "@/lib/kanban";

const API_BASE = "/api";

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { ...authHeaders(), ...init?.headers },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(body || `HTTP ${res.status}`);
  }
  return res.json();
}

function jsonBody(data: unknown): RequestInit {
  return {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  };
}

export async function login(
  username: string,
  password: string
): Promise<{ token: string; username: string }> {
  return apiFetch("/auth/login", jsonBody({ username, password }));
}

export async function fetchMe(): Promise<{ username: string }> {
  return apiFetch("/auth/me");
}

export async function fetchBoard(): Promise<BoardData> {
  return apiFetch("/board");
}

export async function renameColumn(columnId: number, title: string): Promise<BoardData> {
  return apiFetch(`/board/columns/${columnId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
}

export async function createCard(
  columnId: number,
  title: string,
  details: string
): Promise<BoardData> {
  return apiFetch("/board/cards", jsonBody({ column_id: columnId, title, details }));
}

export async function updateCard(
  cardId: number,
  updates: { title?: string; details?: string }
): Promise<BoardData> {
  return apiFetch(`/board/cards/${cardId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  });
}

export async function deleteCard(cardId: number): Promise<BoardData> {
  return apiFetch(`/board/cards/${cardId}`, { method: "DELETE" });
}

export async function moveCard(
  cardId: number,
  columnId: number,
  position: number
): Promise<BoardData> {
  return apiFetch(`/board/cards/${cardId}/move`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ column_id: columnId, position }),
  });
}

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type ChatResponse = {
  message: string;
  board_updates: unknown[];
  board: BoardData;
};

export async function sendChat(
  message: string,
  history: ChatMessage[]
): Promise<ChatResponse> {
  return apiFetch("/chat", jsonBody({ message, history }));
}
