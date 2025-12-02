"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import P1IncidentSuccess from "@/components/P1IncidentSuccess";

export default function P1SuccessPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [incidentData, setIncidentData] = useState<any>(null);

  useEffect(() => {
    const ticketId = searchParams.get('ticket');
    const incidentId = searchParams.get('incident');
    const subject = searchParams.get('subject');

    if (!ticketId || !incidentId || !subject) {
      // Redirect to home if missing parameters
      router.push('/');
      return;
    }

    // Set incident data immediately - no need for fake loading
    setIncidentData({
      ticketId,
      incidentId,
      subject: decodeURIComponent(subject),
      createdAt: new Date().toISOString()
    });
    setLoading(false);
  }, [searchParams, router]);

  if (loading) {
    return (
      <div className="p1-loading">
        <div className="loading-content">
          <div className="loading-spinner">
            <div className="spinner"></div>
          </div>
          <h2>Setting up P1 Incident Response...</h2>
          <p>Notifying operations team and creating communication channels</p>
        </div>
      </div>
    );
  }

  if (!incidentData) {
    return (
      <div className="p1-error">
        <h2>Incident Not Found</h2>
        <p>Unable to load incident details.</p>
        <button onClick={() => router.push('/')}>Return to Home</button>
      </div>
    );
  }

  return (
    <P1IncidentSuccess 
      ticketId={incidentData.ticketId}
      incidentId={incidentData.incidentId}
      subject={incidentData.subject}
      createdAt={incidentData.createdAt}
    />
  );
}