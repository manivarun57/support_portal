"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { createTicket } from "@/lib/api";

export default function P1CriticalPage() {
  const router = useRouter();
  const [formState, setFormState] = useState({
    subject: "",
    priority: "P1",
    category: "P1 Critical Incident",
    description: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    
    try {
      const response = await createTicket(formState);
      // Redirect to the created ticket
      router.push(`/tickets/${response.ticket.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unable to create P1 incident");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p1-critical-container">
      {/* Header */}
      <div className="p1-header">
        <div className="p1-alert-icon">⚠️</div>
        <h1 className="p1-title">Report P1 Critical Incident</h1>
        <p className="p1-subtitle">
          This will immediately notify the operations team and create a dedicated Slack channel
        </p>
      </div>

      {/* Form */}
      <form className="p1-form" onSubmit={handleSubmit}>
        <div className="form-field">
          <label htmlFor="incident-title" className="form-label">
            Incident Title <span className="required">*</span>
          </label>
          <input
            id="incident-title"
            type="text"
            className="form-input"
            placeholder="e.g., Payment Gateway Down - All Transactions Failing"
            value={formState.subject}
            onChange={(e) => setFormState(prev => ({ ...prev, subject: e.target.value }))}
            required
          />
        </div>

        <div className="form-field">
          <label htmlFor="description" className="form-label">
            Detailed Description <span className="required">*</span>
          </label>
          <textarea
            id="description"
            className="form-textarea"
            placeholder="Describe the issue in detail: What happened? When did it start? What is the business impact? Include any error messages or codes."
            rows={6}
            value={formState.description}
            onChange={(e) => setFormState(prev => ({ ...prev, description: e.target.value }))}
            required
          />
        </div>

        {/* What happens next section */}
        <div className="workflow-section">
          <div className="workflow-header">
            <span className="workflow-icon">⚠️</span>
            <span className="workflow-title">What happens next?</span>
          </div>
          <ol className="workflow-list">
            <li>Operations team receives immediate notification</li>
            <li>Dedicated Slack channel created for real-time communication</li>
            <li>Senior engineer assigned within 2 minutes</li>
            <li>Regular status updates every 15 minutes</li>
          </ol>
        </div>

        {/* Action buttons */}
        <div className="form-actions">
          <button
            type="submit"
            className="btn-create-incident"
            disabled={submitting}
          >
            <span className="btn-icon">⚠️</span>
            {submitting ? "Creating P1 Incident..." : "Create P1 Incident"}
          </button>
          <button
            type="button"
            className="btn-cancel"
            onClick={() => router.back()}
          >
            Cancel
          </button>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
      </form>
    </div>
  );
}