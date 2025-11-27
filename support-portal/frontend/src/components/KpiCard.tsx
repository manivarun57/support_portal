"use client";

type Props = {
  label: string;
  value: number | string;
  subtitle?: string;
  icon?: string;
  variant?: 'default' | 'success' | 'info' | 'purple';
};

export function KpiCard({ label, value, subtitle, icon, variant = 'default' }: Props) {
  const getVariantClass = () => {
    switch (variant) {
      case 'success': return 'kpi-card-success';
      case 'info': return 'kpi-card-info';
      case 'purple': return 'kpi-card-purple';
      default: return '';
    }
  };

  return (
    <div className={`card ${getVariantClass()}`}>
      <div className="kpi-header">
        {icon && <span className="kpi-icon">{icon}</span>}
        <p className="card-title">{label}</p>
      </div>
      <p className="card-value">{value}</p>
      {subtitle && (
        <p className="card-subtitle">{subtitle}</p>
      )}
    </div>
  );
}

