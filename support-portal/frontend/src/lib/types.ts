export type Metrics = {
  total: number;
  open: number;
  resolved: number;
};

export type Ticket = {
  id: string;
  subject: string;
  priority: "low" | "medium" | "high" | "P1";
  category: string;
  description: string;
  status: string;
  user_id: string;
  created_at: string;
  attachment_url?: string | null;
  p1_incident?: {
    incident_id: string;
    status: string;
  };
};

export type P1Incident = {
  id: string;
  ticket_id: string;
  incident_id: string;
  status: string;
  created_at: string;
  resolved_at?: string | null;
};

export type CreateTicketResponse = {
  ticket: Ticket;
  p1_incident?: P1Incident;
  slack_notification?: "sent" | "failed";
};

export type Comment = {
  id: string;
  ticket_id: string;
  user_id: string;
  comment: string;
  created_at: string;
};

