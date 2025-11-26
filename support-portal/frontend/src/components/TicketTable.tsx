"use client";

import { format } from "date-fns";
import { Ticket } from "@/lib/types";

type Props = {
  tickets: Ticket[];
  onRowClick?: (ticketId: string) => void;
};

export function TicketTable({ tickets, onRowClick }: Props) {
  return (
    <div className="table-container">
      <div className="table-wrapper">
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
                <td colSpan={5} className="empty-state">
                  <div className="empty-content">
                    <svg viewBox="0 0 24 24" fill="none" width="48" height="48">
                      <path d="M9 11H15M9 15H15M17 21H7C5.89543 21 5 20.1046 5 19V5C5 3.89543 5.89543 3 7 3H12.5858C12.851 3 13.1054 3.10536 13.2929 3.29289L19.7071 9.70711C19.8946 9.89464 20 10.149 20 10.4142V19C20 20.1046 19.1046 21 18 21H17Z" stroke="currentColor" strokeWidth="1.5"/>
                    </svg>
                    <p>No tickets yet</p>
                    <small>Your support tickets will appear here once created</small>
                  </div>
                </td>
              </tr>
            ) : (
              tickets.map((ticket) => (
                <tr
                  key={ticket.id}
                  className="clickable-row"
                  onClick={() => onRowClick?.(ticket.id)}
                >
                  <td>
                    <div className="ticket-subject">
                      {ticket.subject}
                    </div>
                  </td>
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
                  <td className="date-cell">
                    {format(
                      new Date(ticket.created_at),
                      "MMM dd, yyyy"
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

