import { Comment, Metrics, Ticket, CreateTicketResponse } from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function getCurrentUserId(): string {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('selectedUserId') || 
           (window as any).NEXT_PUBLIC_DEFAULT_USER_ID || 
           process.env.NEXT_PUBLIC_DEFAULT_USER_ID || 
           "demo-user";
  }
  return process.env.NEXT_PUBLIC_DEFAULT_USER_ID ?? "demo-user";
}

function getAuthToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('authToken');
  }
  return null;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  
  // Use authentication token if available, otherwise fall back to X-User-Id
  const authToken = getAuthToken();
  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
  } else {
    headers.set("X-User-Id", getCurrentUserId());
  }

  const isJsonBody =
    init?.body && !(init.body instanceof FormData) && !headers.has("Content-Type");
  if (isJsonBody || !init?.body) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    let message = "Request failed";
    try {
      const payload = await response.json();
      message = payload?.message || JSON.stringify(payload);
    } catch {
      // ignore
    }
    throw new Error(message);
  }

  return response.json();
}

export async function fetchDashboardMetrics(): Promise<Metrics> {
  const data = await apiFetch<{ metrics: Metrics }>("/dashboard/metrics");
  return data.metrics;
}

export async function fetchMyTickets(): Promise<Ticket[]> {
  const data = await apiFetch<{ tickets: Ticket[] }>("/tickets/my");
  return data.tickets;
}

export async function fetchTicket(ticketId: string): Promise<Ticket> {
  const data = await apiFetch<{ ticket: Ticket }>(`/tickets/${ticketId}`);
  return data.ticket;
}

export async function fetchTicketComments(ticketId: string): Promise<Comment[]> {
  const data = await apiFetch<{ comments: Comment[] }>(
    `/tickets/${ticketId}/comments`,
  );
  return data.comments;
}

type CreateTicketInput = {
  subject: string;
  priority: string;
  category: string;
  description: string;
  attachment?: string | null;
  attachment_name?: string;
  attachment_type?: string;
};

export async function createTicket(payload: CreateTicketInput): Promise<CreateTicketResponse> {
  return apiFetch<CreateTicketResponse>("/tickets", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

type CreateCommentInput = {
  comment: string;
};

export async function createComment(ticketId: string, payload: CreateCommentInput) {
  return apiFetch<{ comment: Comment }>(`/tickets/${ticketId}/comments`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

type UpdateTicketStatusInput = {
  status: "open" | "in_progress" | "resolved" | "closed";
  resolution_note?: string;
};

export async function updateTicketStatus(ticketId: string, payload: UpdateTicketStatusInput) {
  return apiFetch<{ success: boolean; message: string; ticket_id: string; status: string }>(`/tickets/${ticketId}/status`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function fetchP1Incident(incidentId: string) {
  const data = await apiFetch<{ p1_incident: any }>(`/p1-incidents/by-incident/${incidentId}`);
  return data.p1_incident;
}

export async function fetchP1IncidentByTicket(ticketId: string) {
  try {
    const data = await apiFetch<{ p1_incident: any }>(`/p1-incidents/by-ticket/${ticketId}`);
    return data.p1_incident;
  } catch (error) {
    // Return null if no P1 incident exists for this ticket
    return null;
  }
}

