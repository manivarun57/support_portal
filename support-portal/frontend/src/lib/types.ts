export type Metrics = {
  total: number;
  open: number;
  resolved: number;
};

export type Ticket = {
  id: string;
  subject: string;
  priority: "low" | "medium" | "high";
  category: string;
  description: string;
  status: string;
  user_id: string;
  created_at: string;
  attachment_url?: string | null;
};

export type Comment = {
  id: string;
  ticket_id: string;
  user_id: string;
  comment: string;
  created_at: string;
};

