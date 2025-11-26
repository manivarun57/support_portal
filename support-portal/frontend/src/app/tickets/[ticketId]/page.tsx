"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CommentList } from "@/components/CommentList";
import { PageHeader } from "@/components/PageHeader";
import { fetchTicket, fetchTicketComments } from "@/lib/api";
import { Comment, Ticket } from "@/lib/types";

type Props = {
  params: { ticketId: string };
};

export default function TicketDetailsPage({ params }: Props) {
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    Promise.all([
      fetchTicket(params.ticketId),
      fetchTicketComments(params.ticketId),
    ])
      .then(([ticketPayload, commentPayload]) => {
        if (!isMounted) return;
        setTicket(ticketPayload);
        setComments(commentPayload);
      })
      .catch((err: unknown) => {
        if (!isMounted) return;
        setError(err instanceof Error ? err.message : "Failed to load ticket");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [params.ticketId]);

  if (loading) {
    return <div className="section-card">Loading ticket…</div>;
  }

  if (error) {
    return (
      <div className="section-card" style={{ color: "#b91c1c" }}>
        {error}
      </div>
    );
  }

  if (!ticket) {
    return <div className="section-card">Ticket not found.</div>;
  }

  return (
    <>
      <PageHeader
        title={ticket.subject}
        subtitle={`Status: ${ticket.status}`}
        actions={
          <Link href="/tickets" className="btn btn-secondary">
            Back to tickets
          </Link>
        }
      />

      <div className="section-card" style={{ marginBottom: "1.5rem" }}>
        <p>
          <strong>Priority:</strong>{" "}
          <span className={`pill pill-${ticket.priority}`}>
            {ticket.priority}
          </span>
        </p>
        <p>
          <strong>Category:</strong> {ticket.category}
        </p>
        <p style={{ marginTop: "1rem", color: "#475569" }}>
          {ticket.description}
        </p>
        {ticket.attachment_url ? (
          <p style={{ marginTop: "1rem" }}>
            <a href={ticket.attachment_url} className="btn btn-secondary">
              View Attachment
            </a>
          </p>
        ) : null}
      </div>

      <h2 style={{ marginBottom: "0.75rem" }}>Comments</h2>
      <CommentList comments={comments} />
    </>
  );
}

