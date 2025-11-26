import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { SidebarNav } from "@/components/SidebarNav";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Support Portal",
  description: "Internal dashboard for ticketing KPIs and requests",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        <div className="app-shell">
          <aside className="sidebar">
            <div className="brand">
              <span className="brand-icon">SP</span>
              <div>
                <h1>Support Portal</h1>
                <p style={{ margin: 0, color: "#94a3b8" }}>
                  Pi Client Hub
                </p>
              </div>
            </div>
            <SidebarNav />
          </aside>
          <div className="main-pane">
            <main>{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
