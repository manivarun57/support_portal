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

      {loading && <div className="section-card">Loading tickets…</div>}
      {error && (
        <div className="section-card" style={{ color: "#b91c1c" }}>
          {error}
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

