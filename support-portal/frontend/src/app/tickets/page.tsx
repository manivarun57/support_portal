"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { TicketTable } from "@/components/TicketTable";
import { fetchMyTickets } from "@/lib/api";
import { Ticket } from "@/lib/types";

export default function MyTicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    let isMounted = true;

    fetchMyTickets()
      .then((data) => {
        if (isMounted) setTickets(data);
      })
      .catch((err: unknown) => {
        if (isMounted) {
          setError(
            err instanceof Error ? err.message : "Failed to load tickets",
          );
        }
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <>
      <PageHeader
        title="My Tickets"
        subtitle="All requests submitted under your account."
        actions={
          <Link href="/tickets/create" className="btn btn-primary">
            New Ticket
          </Link>
        }
      />

      {loading && (
        <div className="loading-card">
          <div className="loading-spinner">
            <div className="spinner"></div>
          </div>
          <p>Loading tickets…</p>
        </div>
      )}
      {error && (
        <div className="error-card">
          <div className="error-icon">
            <svg viewBox="0 0 24 24" fill="none" width="24" height="24">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
              <path d="m15 9-6 6" stroke="currentColor" strokeWidth="2"/>
              <path d="m9 9 6 6" stroke="currentColor" strokeWidth="2"/>
            </svg>
          </div>
          <div>
            <h3>Failed to Load Tickets</h3>
            <p>{error}</p>
            <p className="error-hint">Please check your connection and try refreshing the page.</p>
          </div>
        </div>
      )}

      {!loading && !error && (
        <TicketTable
          tickets={tickets}
          onRowClick={(ticketId) => router.push(`/tickets/${ticketId}`)}
        />
      )}
    </>
  );
}

