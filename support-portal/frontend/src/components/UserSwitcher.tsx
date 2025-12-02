"use client";

import { useState } from "react";

export default function UserSwitcher() {
  const [isOpen, setIsOpen] = useState(false);

  const testUsers = [
    { username: "john.doe", password: "password123", merchant: "TechCorp", role: "Admin", fullName: "John Doe", email: "john.doe@techcorp.com" },
    { username: "sarah.smith", password: "password123", merchant: "TechCorp", role: "User", fullName: "Sarah Smith", email: "sarah.smith@techcorp.com" },
    { username: "dheeraj", password: "password123", merchant: "TechCorp", role: "User", fullName: "Dheeraj", email: "dheeraj.narayanam@payintelli.com" },
    { username: "alice.wong", password: "password123", merchant: "ShopifyPlus", role: "Admin", fullName: "Alice Wong", email: "alice.wong@shopifyplus.com" },
    { username: "bob.martin", password: "password123", merchant: "ShopifyPlus", role: "User", fullName: "Bob Martin", email: "bob.martin@shopifyplus.com" },
    { username: "emma.davis", password: "password123", merchant: "FinanceOne", role: "Admin", fullName: "Emma Davis", email: "emma.davis@financeone.com" },
  ];

  const handleLogin = async (user: typeof testUsers[0]) => {
    try {
      const response = await fetch("http://localhost:8000/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: user.username, password: user.password }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        localStorage.setItem("authToken", data.data.token);
        localStorage.setItem("userInfo", JSON.stringify(data.data.user));
        window.location.reload();
      } else {
        alert("Login failed: " + (data.message || "Unknown error"));
      }
    } catch (err) {
      console.error("Login error:", err);
      alert("Failed to connect to server");
    }
  };

  return (
    <div className="px-3 py-3">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3 py-2 bg-blue-600 text-white text-xs font-medium rounded-lg hover:bg-blue-700 transition"
      >
        Switch User/Merchant
      </button>

      {isOpen && (
        <div className="mt-2 bg-white border border-gray-200 rounded-lg shadow-lg p-3 space-y-2 max-h-96 overflow-y-auto">
          <div className="text-xs font-semibold text-gray-700 mb-2 pb-2 border-b">
            Select Test User
          </div>
          {testUsers.map((user) => (
            <button
              key={user.username}
              onClick={() => {
                handleLogin(user);
                setIsOpen(false);
              }}
              className="w-full text-left px-3 py-2 rounded-md hover:bg-blue-50 border border-gray-200 transition"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs font-semibold text-gray-900">{user.fullName}</div>
                  <div className="text-[10px] text-gray-500">{user.email}</div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] font-medium text-blue-600">{user.merchant}</div>
                  <div className={`text-[9px] px-1.5 py-0.5 rounded ${user.role === 'Admin' ? 'bg-purple-100 text-purple-700' : 'bg-green-100 text-green-700'}`}>
                    {user.role}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
