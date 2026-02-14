const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let token: string | null = null;

export function setToken(t: string | null) {
  token = t;
}

export function getToken() {
  return token;
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Don't set Content-Type for FormData (browser sets it with boundary)
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }

  return res.json();
}

// Auth
export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export function register(email: string, password: string) {
  return request<AuthResponse>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function login(email: string, password: string) {
  return request<AuthResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function getMe() {
  return request<User>("/api/auth/me");
}

// Reports
export interface Report {
  id: string;
  user_id: string;
  status: string;
  image_url: string | null;
  findings: string | null;
  research_results: string | null;
  final_report: string | null;
  safety_review: string | null;
  confidence_score: number | null;
  created_at: string;
  updated_at: string;
}

export function uploadImage(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return request<Report>("/api/upload", {
    method: "POST",
    body: formData,
  });
}

export function getReports() {
  return request<Report[]>("/api/reports");
}

export function getReport(id: string) {
  return request<Report>(`/api/reports/${id}`);
}

// Generate report (HTTP – non-streaming)
export function generateReport(reportId: string) {
  return request<Report>(`/api/reports/${reportId}/generate`, {
    method: "POST",
  });
}

// Pipeline WebSocket status messages
export interface PipelineMessage {
  type: "pipeline_started" | "status" | "pipeline_complete" | "error";
  step?: string;
  status?: string;
  report_id?: string;
  has_findings?: boolean;
  safety_passed?: boolean;
  retry_count?: number;
  detail?: string;
}

/**
 * Start the report generation pipeline over WebSocket for real-time
 * status updates.  Returns the WebSocket instance so the caller can
 * close it if needed.
 */
export function generateReportWs(
  reportId: string,
  onMessage: (msg: PipelineMessage) => void,
  onError?: (err: Event) => void,
  onClose?: () => void
): WebSocket {
  const wsUrl = API_URL.replace(/^http/, "ws");
  const ws = new WebSocket(
    `${wsUrl}/ws/reports/${reportId}?token=${token}`
  );

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data) as PipelineMessage;
      onMessage(data);
    } catch {
      // ignore parse errors
    }
  };

  ws.onerror = (event) => {
    onError?.(event);
  };

  ws.onclose = () => {
    onClose?.();
  };

  return ws;
}
