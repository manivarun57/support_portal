"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import P1IncidentSuccess from "@/components/P1IncidentSuccess";
import { fetchP1Incident } from "@/lib/api";

export default function P1IncidentPage() {
  const params = useParams();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [incidentData, setIncidentData] = useState<any>(null);

  useEffect(() => {
    const incidentId = params.incident_id as string;
    
    if (!incidentId) {
      router.push('/');
      return;
    }

    // Fetch incident details from backend
    const loadIncident = async () => {
      try {
        console.log('Fetching incident:', incidentId);
        const incident = await fetchP1Incident(incidentId);
        console.log('Incident data:', incident);

        setIncidentData({
          ticketId: incident.ticket_id,
          incidentId: incident.incident_id,
          subject: incident.ticket.subject,
          createdAt: incident.created_at,
          status: incident.status
        });
      } catch (err) {
        console.error('Error loading incident:', err);
        setError(err instanceof Error ? err.message : 'Failed to load incident');
      } finally {
        setLoading(false);
      }
    };

    loadIncident();
  }, [params.incident_id, router]);

  if (loading) {
    return (
      <div className="p1-loading">
        <div className="loading-content">
          <div className="loading-spinner">
            <div className="spinner"></div>
          </div>
          <h2>Loading P1 Incident...</h2>
          <p>Retrieving incident details and communication history</p>
        </div>
      </div>
    );
  }

  if (error || !incidentData) {
    return (
      <div className="p1-error">
        <div className="error-icon">⚠️</div>
        <h2>Unable to Load Incident</h2>
        <p>{error || 'Incident not found'}</p>
        <button 
          onClick={() => router.push('/tickets')}
          className="btn btn-primary"
        >
          Return to My Tickets
        </button>
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
