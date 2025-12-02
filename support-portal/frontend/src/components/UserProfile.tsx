"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

interface UserInfo {
  user_id: string;
  username: string;
  full_name: string;
  email: string;
  merchant_name: string;
  company_name: string;
  role: string;
}

export default function UserProfile() {
  const router = useRouter();
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [showMenu, setShowMenu] = useState(false);

  useEffect(() => {
    const storedUserInfo = localStorage.getItem("userInfo");
    if (storedUserInfo) {
      setUserInfo(JSON.parse(storedUserInfo));
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("authToken");
    localStorage.removeItem("userInfo");
    router.push("/login");
  };

  if (!userInfo) {
    return (
      <div className="px-3 py-4 text-center text-xs text-gray-500">
        <div className="rounded-lg border border-dashed border-gray-300 p-4 bg-gray-50">
          <p className="font-medium mb-1">Authentication Disabled</p>
          <p className="text-[11px] leading-relaxed">Login page was removed. Local features will run in guest mode.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="px-3 py-3">
      <div className="bg-gradient-to-br from-white to-blue-50 rounded-xl shadow-md border border-blue-100 overflow-hidden">
        {/* User Info */}
        <div className="p-4">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center text-white font-bold text-sm shadow-lg">
                {userInfo.full_name.split(" ").map(n => n[0]).join("")}
              </div>
              <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white"></div>
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm font-bold text-gray-900 truncate">
                  {userInfo.full_name}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                  userInfo.role === 'admin' 
                    ? 'bg-purple-100 text-purple-700 border border-purple-200' 
                    : 'bg-blue-100 text-blue-700 border border-blue-200'
                }`}>
                  {userInfo.role.charAt(0).toUpperCase() + userInfo.role.slice(1)}
                </span>
              </div>
              <div className="text-xs text-gray-600 font-medium truncate">
                {userInfo.company_name}
              </div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="border-t border-blue-100 bg-gradient-to-r from-blue-50 to-indigo-50 px-4 py-3">
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 text-xs text-gray-500 hover:text-gray-700 font-medium py-1.5 rounded-md transition"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            Guest Mode Logout
          </button>
        </div>
      </div>
    </div>
  );
}
