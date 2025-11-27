"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { createTicket } from "@/lib/api";

export default function P1CriticalPage() {
  const router = useRouter();
  const [formState, setFormState] = useState({
    subject: "",
    priority: "P1", // Fixed to P1 priority
    category: "P1 Critical Incident",
    description: "",
  });
  const [fileData, setFileData] = useState<{
    attachment?: string;
    attachment_name?: string;
    attachment_type?: string;
  }>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      setFileData({});
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      setFileData({
        attachment: (reader.result as string).split(",")[1],
        attachment_name: file.name,
        attachment_type: file.type,
      });
    };
    reader.readAsDataURL(file);
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const payload = {
        ...formState,
        ...fileData,
      };
      const response = await createTicket(payload);
      setSuccess("P1 Critical ticket created successfully!");
      setTimeout(() => router.push(`/tickets/${response.ticket.id}`), 800);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unable to create P1 ticket");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <PageHeader
        title="🚨 P1 Critical Incident"
        subtitle="For critical incidents requiring immediate attention. This will create a high-priority ticket."
      />

      <div className="section-card" style={{ backgroundColor: "#fef2f2", borderColor: "#dc2626" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem" }}>
          <span style={{ fontSize: "1.5rem" }}>⚠️</span>
          <strong style={{ color: "#dc2626" }}>Critical Incident Guidelines</strong>
        </div>
        <ul style={{ color: "#7f1d1d", margin: 0, paddingLeft: "1.5rem" }}>
          <li>Use only for production-impacting issues</li>
          <li>Service outages or critical functionality failures</li>
          <li>Security incidents requiring immediate response</li>
          <li>Data integrity or customer-facing critical issues</li>
        </ul>
      </div>

      <form className="section-card" onSubmit={handleSubmit}>
        <div>
          <label htmlFor="subject">
            Incident Summary <span style={{ color: "#dc2626" }}>*</span>
          </label>
          <input
            id="subject"
            name="subject"
            value={formState.subject}
            onChange={(e) =>
              setFormState((prev) => ({ ...prev, subject: e.target.value }))
            }
            placeholder="Brief description of the critical issue"
            required
          />
        </div>

        <div>
          <label htmlFor="priority">Priority</label>
          <input
            id="priority"
            name="priority"
            value="P1 - Critical"
            disabled
            style={{ backgroundColor: "#f9fafb", color: "#374151" }}
          />
          <small style={{ color: "#6b7280" }}>
            Fixed to P1 Critical priority for immediate escalation
          </small>
        </div>

        <div>
          <label htmlFor="category">Category</label>
          <input
            id="category"
            name="category"
            value={formState.category}
            onChange={(e) =>
              setFormState((prev) => ({ ...prev, category: e.target.value }))
            }
            placeholder="P1 Critical Incident"
          />
        </div>

        <div>
          <label htmlFor="description">
            Detailed Description <span style={{ color: "#dc2626" }}>*</span>
          </label>
          <textarea
            id="description"
            name="description"
            value={formState.description}
            onChange={(e) =>
              setFormState((prev) => ({ ...prev, description: e.target.value }))
            }
            placeholder="Provide detailed information about:
• What is the impact?
• When did it start?
• What steps have been taken?
• Any error messages or logs?"
            rows={6}
            required
          />
        </div>

        <div>
          <label htmlFor="attachment">Supporting Files (logs, screenshots, etc.)</label>
          <input id="attachment" type="file" onChange={handleFileChange} />
        </div>

        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
          <button 
            className="btn btn-primary" 
            type="submit" 
            disabled={submitting}
            style={{ backgroundColor: "#dc2626", borderColor: "#dc2626" }}
          >
            {submitting ? "Creating P1 Ticket..." : "🚨 Submit P1 Critical Ticket"}
          </button>
          {error && <span style={{ color: "#b91c1c" }}>{error}</span>}
          {success && <span style={{ color: "#16a34a" }}>{success}</span>}
        </div>
      </form>
    </>
  );
}