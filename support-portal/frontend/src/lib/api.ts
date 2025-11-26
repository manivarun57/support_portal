import { Comment, Metrics, Ticket } from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const DEFAULT_USER_ID =
  process.env.NEXT_PUBLIC_DEFAULT_USER_ID ?? "demo-user";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("X-User-Id", DEFAULT_USER_ID);

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

export async function createTicket(payload: CreateTicketInput) {
  return apiFetch<{ ticket: Ticket }>("/tickets", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

