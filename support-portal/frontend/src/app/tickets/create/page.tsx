"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { createTicket } from "@/lib/api";

const priorities = [
  { label: "Low", value: "low" },
  { label: "Medium", value: "medium" },
  { label: "High", value: "high" },
  { label: "P1 Critical", value: "P1" },
];

export default function CreateTicketPage() {
  const router = useRouter();
  const [formState, setFormState] = useState({
    subject: "",
    priority: "medium",
    category: "",
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
      setSuccess("Ticket created successfully!");
      setTimeout(() => router.push(`/tickets/${response.ticket.id}`), 800);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unable to create ticket");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Create Ticket"
        subtitle="Provide as much detail as possible to help the support team triage faster."
      />

      <form className="section-card" onSubmit={handleSubmit}>
        <div>
          <label htmlFor="subject">Subject</label>
          <input
            id="subject"
            name="subject"
            value={formState.subject}
            onChange={(e) =>
              setFormState((prev) => ({ ...prev, subject: e.target.value }))
            }
            required
          />
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
            placeholder="Billing, Access, Incident, etc."
            required
          />
        </div>

        <div>
          <label htmlFor="priority">Priority</label>
          <select
            id="priority"
            name="priority"
            value={formState.priority}
            onChange={(e) =>
              setFormState((prev) => ({ ...prev, priority: e.target.value }))
            }
          >
            {priorities.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            name="description"
            value={formState.description}
            onChange={(e) =>
              setFormState((prev) => ({ ...prev, description: e.target.value }))
            }
            required
          />
        </div>

        <div>
          <label htmlFor="attachment">Attachment (optional)</label>
          <input id="attachment" type="file" onChange={handleFileChange} />
        </div>

        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {submitting ? "Submitting..." : "Submit Ticket"}
          </button>
          {error && <span style={{ color: "#b91c1c" }}>{error}</span>}
          {success && <span style={{ color: "#16a34a" }}>{success}</span>}
        </div>
      </form>
    </>
  );
}

