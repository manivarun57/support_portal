"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import SlackIntegration from "@/components/SlackIntegration";

interface P1IncidentSuccessProps {
  ticketId: string;
  incidentId: string;
  subject: string;
  createdAt: string;
}

export default function P1IncidentSuccess({ ticketId, incidentId, subject, createdAt }: P1IncidentSuccessProps) {
  const router = useRouter();
  const [responseTime, setResponseTime] = useState(120); // 2 minutes countdown
  const [opsTeamSize, setOpsTeamSize] = useState(3);

  useEffect(() => {
    const timer = setInterval(() => {
      setResponseTime(prev => Math.max(0, prev - 1));
    }, 1000);

    // Simulate ops team joining
    const teamTimer = setTimeout(() => {
      setOpsTeamSize(prev => prev + 2);
    }, 3000);

    return () => {
      clearInterval(timer);
      clearTimeout(teamTimer);
    };
  }, []);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="p1-success-container">
      {/* Success Header */}
      <div className="success-header">
        <div className="success-icon">✅</div>
        <h1 className="success-title">P1 Critical Incident Created</h1>
        <p className="success-subtitle">
          Your incident has been escalated to the operations team
        </p>
      </div>

      {/* Incident Details */}
      <div className="incident-summary">
        <div className="incident-badge">
          <span className="badge-label">ACTIVE P1</span>
          <span className="incident-id">{incidentId}</span>
        </div>
        
        <div className="incident-info">
          <h2 className="incident-subject">{subject}</h2>
          <div className="incident-meta">
            <span className="meta-item">
              <span className="icon">🕐</span>
              Created {new Date(createdAt).toLocaleString()}
            </span>
            <span className="meta-item">
              <span className="icon">👥</span>
              {opsTeamSize} Ops Team Online
            </span>
            <span className="meta-item">
              <span className="icon">⏱️</span>
              Avg Response Time: {formatTime(responseTime)}
            </span>
          </div>
        </div>
      </div>

      {/* Response Timeline */}
      <div className="response-timeline">
        <h3>Response Timeline</h3>
        <div className="timeline-items">
          <div className="timeline-item completed">
            <div className="timeline-dot"></div>
            <div className="timeline-content">
              <span className="timeline-title">Incident Reported</span>
              <span className="timeline-time">Just now</span>
            </div>
          </div>
          
          <div className="timeline-item active">
            <div className="timeline-dot"></div>
            <div className="timeline-content">
              <span className="timeline-title">Operations Team Notified</span>
              <span className="timeline-time">In progress</span>
            </div>
          </div>
          
          <div className="timeline-item pending">
            <div className="timeline-dot"></div>
            <div className="timeline-content">
              <span className="timeline-title">Senior Engineer Assigned</span>
              <span className="timeline-time">Within 2 minutes</span>
            </div>
          </div>
          
          <div className="timeline-item pending">
            <div className="timeline-dot"></div>
            <div className="timeline-content">
              <span className="timeline-title">Status Updates Begin</span>
              <span className="timeline-time">Every 15 minutes</span>
            </div>
          </div>
        </div>
      </div>

      {/* Slack Integration */}
      <SlackIntegration 
        key={incidentId}
        incidentId={incidentId}
        ticketId={ticketId}
        onChannelReady={(channel) => {
          console.log('Slack channel ready:', channel);
        }}
        onIncidentResolved={() => {
          // Show success notification
          alert('✅ P1 Incident resolved successfully! The ticket has been updated to "resolved" status.');
          
          // Optionally redirect to tickets page
          setTimeout(() => {
            window.location.href = '/tickets';
          }, 2000);
        }}
      />

      {/* Actions */}
      <div className="success-actions">
        <button 
          className="btn-view-ticket"
          onClick={() => router.push(`/tickets/${ticketId}`)}
        >
          <span className="btn-icon">📋</span>
          View Full Ticket Details
        </button>
        
        <button 
          className="btn-my-tickets"
          onClick={() => router.push('/tickets')}
        >
          <span className="btn-icon">📊</span>
          Go to My Tickets
        </button>
        
        <button 
          className="btn-home"
          onClick={() => router.push('/')}
        >
          <span className="btn-icon">🏠</span>
          Return to Dashboard
        </button>
      </div>

      {/* Emergency Contact */}
      <div className="emergency-contact">
        <div className="emergency-header">
          <span className="emergency-icon">🚨</span>
          <span>Emergency Escalation</span>
        </div>
        <p className="emergency-text">
          If this is a life-threatening emergency or complete system failure:
        </p>
        <div className="emergency-contacts">
          <a href="tel:+15559111111" className="emergency-btn">
            📞 Call 24/7 Hotline: +1 (555) 911-P1P1
          </a>
          <a href="mailto:p1@yourcompany.com" className="emergency-btn">
            📧 Email: p1@yourcompany.com
          </a>
        </div>
      </div>
    </div>
  );
}