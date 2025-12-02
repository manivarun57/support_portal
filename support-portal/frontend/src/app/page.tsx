"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { KpiCard } from "@/components/KpiCard";
import { fetchDashboardMetrics } from "@/lib/api";
import { Metrics } from "@/lib/types";

export default function Home() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    fetchDashboardMetrics()
      .then((data) => {
        if (isMounted) {
          setMetrics(data);
        }
      })
      .catch((err: unknown) => {
        if (isMounted) {
          setError(
            err instanceof Error ? err.message : "Failed to load metrics",
          );
        }
      })
      .finally(() => {
        if (isMounted) {
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <>
      <div className="hero-card">
        <div>
          <p className="hero-eyebrow">Support overview</p>
          <h1>Welcome to Support Portal</h1>
          <p>
            Get help quickly, keep an eye on your queue, and create new tickets
            in seconds.
          </p>
          <div className="hero-actions">
            <Link href="/tickets/create" className="btn btn-primary">
              Create Ticket
            </Link>
            <Link href="/tickets" className="btn btn-outline">
              View My Tickets
            </Link>
          </div>
        </div>
        <div className="hero-highlight">
          <p className="card-title">Open tickets</p>
          <p className="card-value">
            {loading ? "…" : metrics?.open ?? "—"}
          </p>
          <p className="ticket-status">Awaiting response</p>
        </div>
      </div>

      {error ? (
        <div className="error-card">
          <div className="error-icon">
            <svg viewBox="0 0 24 24" fill="none" width="24" height="24">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
              <path d="m15 9-6 6" stroke="currentColor" strokeWidth="2"/>
              <path d="m9 9 6 6" stroke="currentColor" strokeWidth="2"/>
            </svg>
          </div>
          <div>
            <h3>Connection Error</h3>
            <p>{error}</p>
            <p className="error-hint">Please check your backend connection and try again.</p>
          </div>
        </div>
      ) : (
        <>
          <div className="card-grid">
            <KpiCard
              label="System Uptime"
              value="98.7%"
              subtitle="All systems operational"
              icon="✓"
              variant="success"
            />
            <KpiCard
              label="Avg P1 Response"
              value="1.8 min"
              subtitle="Critical incident response"
              icon="🕐"
              variant="info"
            />
            <KpiCard
              label="Ops Team Available"
              value="24/7"
              subtitle="Always ready to help"
              icon="👥"
              variant="purple"
            />
          </div>

          {/* P1 Critical Incident Status */}
          <div className="section-card p1-status-card">
            <div className="p1-content">
              <div className="p1-status-icon">⚠️</div>
              <h2 className="p1-status-title">
                No Active P1 Incidents
              </h2>
              <p className="p1-status-description">
                All systems operational. If you're experiencing a critical issue, report it immediately.
              </p>
            </div>
            <Link 
              href="/p1-critical" 
              className="btn btn-primary p1-critical-btn"
            >
              ⚠️ Report P1 Critical Incident
            </Link>
          </div>

          <div className="card-grid">
            <KpiCard
              label="Total Tickets"
              value={loading ? "…" : metrics?.total ?? 0}
              subtitle="All time"
            />
            <KpiCard
              label="Open Tickets"
              value={loading ? "…" : metrics?.open ?? 0}
              subtitle="Awaiting response"
            />
            <KpiCard
              label="Resolved Tickets"
              value={loading ? "…" : metrics?.resolved ?? 0}
              subtitle="Closed successfully"
            />
          </div>
        </>
      )}
    </>
  );
}
