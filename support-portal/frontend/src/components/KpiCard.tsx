"use client";

type Props = {
  label: string;
  value: number | string;
  subtitle?: string;
};

export function KpiCard({ label, value, subtitle }: Props) {
  return (
    <div className="card">
      <p className="card-title">{label}</p>
      <p className="card-value">{value}</p>
      {subtitle ? (
        <p style={{ color: "#94a3b8", fontSize: "0.85rem", margin: 0 }}>
          {subtitle}
        </p>
      ) : null}
    </div>
  );
}

