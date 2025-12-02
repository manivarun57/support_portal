"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showTestUsers, setShowTestUsers] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Store token and user info in localStorage
        localStorage.setItem("authToken", data.data.token);
        localStorage.setItem("userInfo", JSON.stringify(data.data.user));
        
        console.log("✅ Login successful:", data.data.user.full_name);
        
        // Redirect to home page
        router.push("/");
      } else {
        setError(data.message || "Invalid username or password");
      }
    } catch (err) {
      console.error("Login error:", err);
      setError("Failed to connect to server. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Test credentials info (actual users in database)
  const testUsers = [
    { username: "john.doe", merchant: "TechCorp", role: "Admin", fullName: "John Doe" },
    { username: "sarah.smith", merchant: "TechCorp", role: "User", fullName: "Sarah Smith" },
    { username: "dheeraj", merchant: "TechCorp", role: "User", fullName: "Dheeraj" },
    { username: "alice.wong", merchant: "ShopifyPlus", role: "Admin", fullName: "Alice Wong" },
    { username: "bob.martin", merchant: "ShopifyPlus", role: "User", fullName: "Bob Martin" },
    { username: "emma.davis", merchant: "FinanceOne", role: "Admin", fullName: "Emma Davis" },
  ];
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="flex flex-col items-center text-center space-y-2">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-md bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-sm">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h1 className="text-xl font-semibold text-gray-900 tracking-tight">Support Portal</h1>
          </div>
          <p className="text-xs text-gray-500">Secure access to P1 Incident Management</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5 space-y-5">
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label
              htmlFor="username"
              className="block text-xs font-medium text-gray-600 mb-1 uppercase tracking-wide"
            >
              Username
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-3 w-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full pl-9 pr-3 py-2.5 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition text-sm text-gray-900 placeholder-gray-400"
                placeholder="Enter your username"
                required
              />
            </div>
          </div>

          <div>
            <label htmlFor="password" className="block text-xs font-medium text-gray-600 mb-1 uppercase tracking-wide">Password</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-3 w-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-9 pr-3 py-2.5 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition text-sm text-gray-900 placeholder-gray-400"
                placeholder="Enter your password"
                required
              />
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-3 py-2 rounded-md flex items-start">
              <svg className="h-3 w-3 text-red-500 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span className="text-xs">{error}</span>
            </div>
          )}

          <div className="flex items-center justify-between">
            <label className="flex items-center space-x-2 select-none cursor-pointer">
              <input type="checkbox" className="h-3 w-3 text-blue-600 border-gray-300 rounded" />
              <span className="text-[11px] text-gray-600">Remember me</span>
            </label>
            <button type="button" className="text-[11px] text-blue-600 hover:text-blue-700 focus:outline-none">Forgot password?</button>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2.5 rounded-md text-sm font-medium hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-2 h-3 w-3 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Signing in
              </span>
            ) : (
              "Sign In"
            )}
          </button>
        </form>
        </div>
        <div className="pt-1">
          <button
            type="button"
            onClick={()=>setShowTestUsers(!showTestUsers)}
            className="w-full text-[11px] text-gray-600 hover:text-gray-800 flex items-center justify-center space-x-1"
          >
            <svg className={`w-3 h-3 transition-transform ${showTestUsers ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
            <span>{showTestUsers ? 'Hide demo credentials' : 'Show demo credentials'}</span>
          </button>
          {showTestUsers && (
            <div className="mt-2 space-y-1 bg-white border border-gray-200 rounded-md p-3">
              {testUsers.map((u)=> (
                <button
                  key={u.username}
                  type="button"
                  onClick={()=> {setUsername(u.username); setPassword('password123')}}
                  className="w-full flex items-center justify-between text-left text-[11px] px-2 py-1 rounded hover:bg-gray-50"
                >
                  <span className="font-mono text-gray-700">{u.username}</span>
                  <span className="text-gray-500">{u.role}</span>
                </button>
              ))}
              <p className="text-[10px] text-gray-500 pt-1 border-t border-gray-100">Password: password123</p>
            </div>
          )}
        </div>
        <div className="text-center">
          <button type="button" onClick={()=>router.push('/')} className="text-[11px] text-gray-500 hover:text-gray-700">Continue as guest →</button>
        </div>
        <div className="text-center text-[10px] text-gray-400">© {new Date().getFullYear()} Support Portal · Login Build v2</div>
      </div>
    </div>
  );
}
