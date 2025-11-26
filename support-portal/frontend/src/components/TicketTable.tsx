"use client";

import { format } from "date-fns";
import { Ticket } from "@/lib/types";

type Props = {
  tickets: Ticket[];
  onRowClick?: (ticketId: string) => void;
};

export function TicketTable({ tickets, onRowClick }: Props) {
  return (
    <div className="section-card" style={{ padding: 0 }}>
      <table>
        <thead>
          <tr>
            <th>Subject</th>
            <th>Status</th>
            <th>Priority</th>
            <th>Category</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {tickets.length === 0 ? (
            <tr>
              <td colSpan={5} style={{ textAlign: "center", padding: "2rem" }}>
                No tickets yet.
              </td>
            </tr>
          ) : (
            tickets.map((ticket) => (
              <tr
                key={ticket.id}
                style={{ cursor: "pointer" }}
                onClick={() => onRowClick?.(ticket.id)}
              >
                <td>{ticket.subject}</td>
                <td>
                  <span
                    className={`pill pill-${(ticket.status || "open").toLowerCase()}`}
                  >
                    {ticket.status}
                  </span>
                </td>
                <td>
                  <span className={`pill pill-${ticket.priority}`}>
                    {ticket.priority}
                  </span>
                </td>
                <td>{ticket.category}</td>
                <td>
                  {format(
                    new Date(ticket.created_at),
                    "MMM dd, yyyy hh:mm a",
                  )}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

