"use client";

import Link from "next/link";
import { useEffect, useState, use } from "react";
import { CommentList } from "@/components/CommentList";
import { PageHeader } from "@/components/PageHeader";
import { fetchTicket, fetchTicketComments, fetchP1IncidentByTicket } from "@/lib/api";
import { Comment, Ticket } from "@/lib/types";

type Props = {
  params: Promise<{ ticketId: string }>;
};

export default function TicketDetailsPage({ params }: Props) {
  const { ticketId } = use(params);
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [p1Incident, setP1Incident] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    Promise.all([
      fetchTicket(ticketId),
      fetchTicketComments(ticketId),
      fetchP1IncidentByTicket(ticketId),
    ])
      .then(([ticketPayload, commentPayload, p1IncidentPayload]) => {
        if (!isMounted) return;
        setTicket(ticketPayload);
        setComments(commentPayload);
        setP1Incident(p1IncidentPayload);
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
  }, [ticketId]);

  if (loading) {
    return <div className="section-card">Loading ticket…</div>;
  }

  if (error) {
    return (
      <div className="section-card error-card-text">
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

      {/* P1 Critical Incident Alert */}
      {p1Incident && ticket.priority === 'P1' && (
        <div className="p1-incident-alert" style={{
          background: '#fff3cd',
          border: '2px solid #ffc107',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <span style={{ fontSize: '24px' }}>🚨</span>
          <div style={{ flex: 1 }}>
            <strong style={{ color: '#856404', display: 'block', marginBottom: '4px' }}>
              P1 Critical Incident Active
            </strong>
            <span style={{ color: '#856404', fontSize: '14px' }}>
              Incident ID: {p1Incident.incident_id} • Status: {p1Incident.status}
            </span>
          </div>
          <Link 
            href={`/p1-critical/success/${p1Incident.incident_id}`}
            className="btn btn-primary"
            style={{
              background: '#dc3545',
              border: 'none',
              color: 'white',
              padding: '8px 16px',
              borderRadius: '4px',
              textDecoration: 'none',
              fontWeight: '500'
            }}
          >
            💬 Open Chat
          </Link>
        </div>
      )}

      <div className="section-card attachment-card">
        <p>
          <strong>Priority:</strong>{" "}
          <span className={`pill pill-${ticket.priority}`}>
            {ticket.priority}
          </span>
        </p>
        <p>
          <strong>Category:</strong> {ticket.category}
        </p>
        <p className="ticket-description">
          {ticket.description}
        </p>
        {ticket.attachment_url ? (
          <p className="attachment-link">
            <a href={ticket.attachment_url} className="btn btn-secondary">
              View Attachment
            </a>
          </p>
        ) : null}
      </div>

      <h2 className="comments-header">Comments</h2>
      <CommentList 
        comments={comments} 
        ticketId={ticketId}
        onCommentAdded={(newComment) => setComments(prev => [...prev, newComment])}
      />
    </>
  );
}

