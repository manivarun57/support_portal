import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { SidebarNav } from "@/components/SidebarNav";
import UserSelector from "@/components/UserSelector";
import UserProfile from "@/components/UserProfile";
import UserSwitcher from "@/components/UserSwitcher";

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
                <p className="brand-subtitle">
                  Pi Client Hub
                </p>
              </div>
            </div>
            <div className="mt-4">
              <UserProfile />
            </div>
            <UserSwitcher />
            <UserSelector />
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
