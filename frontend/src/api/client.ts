const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

export type RetrievedContext = {
  role: string;
  source: string;
  chunk_id: string;
  text: string;
  score: number;
};

export type Question = {
  turn_id: number;
  question: string;
  topic: string;
  difficulty: string;
  rationale: string;
  retrieved_context: RetrievedContext[];
};

export type SessionStart = {
  session_id: number;
  target_role: string;
  extracted_profile: Record<string, unknown>;
  first_question: Question;
};

export type AnswerResponse = {
  saved_turn_id: number;
  feedback: string;
  answer_score: number;
  next_question: Question | null;
  session_complete: boolean;
};

export type SessionSummary = {
  session_id: number;
  target_role: string;
  status: string;
  extracted_profile: Record<string, unknown>;
  turns: Array<Record<string, unknown>>;
  summary: Record<string, unknown> | null;
  created_at: string;
  completed_at: string | null;
};

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof error.detail === "string" ? error.detail : JSON.stringify(error.detail));
  }
  return response.json();
}

export async function fetchRoles(): Promise<string[]> {
  const response = await fetch(`${API_BASE}/roles`);
  const data = await parseResponse<{ roles: string[] }>(response);
  return data.roles;
}

export async function startSession(form: FormData): Promise<SessionStart> {
  const response = await fetch(`${API_BASE}/sessions`, {
    method: "POST",
    body: form
  });
  return parseResponse<SessionStart>(response);
}

export async function submitAnswer(sessionId: number, turnId: number, answer: string): Promise<AnswerResponse> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}/turns/${turnId}/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answer })
  });
  return parseResponse<AnswerResponse>(response);
}

export async function completeSession(sessionId: number): Promise<SessionSummary> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}/complete`, { method: "POST" });
  return parseResponse<SessionSummary>(response);
}

export async function getSession(sessionId: number): Promise<SessionSummary> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}`);
  return parseResponse<SessionSummary>(response);
}
