"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";

const navItems: { label: string; href: string; icon: ReactNode }[] = [
  {
    label: "Home",
    href: "/",
    icon: (
      <svg viewBox="0 0 24 24" fill="none">
        <path
          d="M4 11L12 4l8 7v8a1 1 0 0 1-1 1h-5v-5H10v5H5a1 1 0 0 1-1-1v-8Z"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
  {
    label: "My Tickets",
    href: "/tickets",
    icon: (
      <svg viewBox="0 0 24 24" fill="none">
        <path
          d="M4 7h16M4 12h16M4 17h10"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
  {
    label: "Create Ticket",
    href: "/tickets/create",
    icon: (
      <svg viewBox="0 0 24 24" fill="none">
        <path
          d="M12 5v14M5 12h14"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
  {
    label: "P1 Critical",
    href: "/p1-critical",
    icon: (
      <svg viewBox="0 0 24 24" fill="none">
        <path
          d="M12 9v4m0 4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
];

export function SidebarNav() {
  const pathname = usePathname();
  return (
    <div className="nav-section">
      {navItems.map((item) => {
        const isActive =
          item.href === "/"
            ? pathname === "/"
            : pathname?.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`nav-link ${isActive ? "active" : ""}`}
          >
            {item.icon}
            <span>{item.label}</span>
          </Link>
        );
      })}
    </div>
  );
}

