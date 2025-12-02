"use client";

import { useState, useEffect } from "react";

interface User {
  id: string;
  name: string;
  email: string;
  department: string;
}

const DEMO_USERS: User[] = [
  { id: "demo-user", name: "Demo User", email: "demo@company.com", department: "Engineering" },
  { id: "john.doe", name: "John Doe", email: "john.doe@company.com", department: "Marketing" },
  { id: "jane.smith", name: "Jane Smith", email: "jane.smith@company.com", department: "Operations" },
  { id: "admin", name: "Admin User", email: "admin@company.com", department: "IT" },
  { id: "sarah.chen", name: "Sarah Chen", email: "sarah.chen@company.com", department: "Engineering" }
];

interface UserSelectorProps {
  onUserChange?: (userId: string) => void;
}

export default function UserSelector({ onUserChange }: UserSelectorProps) {
  const [currentUser, setCurrentUser] = useState<string>('demo-user');
  const [isOpen, setIsOpen] = useState(false);
  const [isClient, setIsClient] = useState(false);

  const selectedUser = DEMO_USERS.find(user => user.id === currentUser) || DEMO_USERS[0];

  useEffect(() => {
    // Initialize client-side state
    setIsClient(true);
    if (typeof window !== 'undefined') {
      const savedUserId = localStorage.getItem('selectedUserId');
      if (savedUserId && savedUserId !== currentUser) {
        setCurrentUser(savedUserId);
      }
    }
  }, []);

  useEffect(() => {
    // Save to localStorage when user changes (only on client)
    if (isClient && typeof window !== 'undefined') {
      localStorage.setItem('selectedUserId', currentUser);
      
      // Update the API default user ID
      (window as any).NEXT_PUBLIC_DEFAULT_USER_ID = currentUser;
    }
    
    onUserChange?.(currentUser);
  }, [currentUser, onUserChange, isClient]);

  const handleUserSelect = (userId: string) => {
    if (userId === currentUser) {
      setIsOpen(false);
      return; // No change needed
    }
    
    setCurrentUser(userId);
    setIsOpen(false);
    
    // Force page reload to use new user context
    if (typeof window !== 'undefined') {
      window.location.reload();
    }
  };

  // Don't render until client-side to avoid hydration mismatch
  if (!isClient) {
    return (
      <div className="user-selector">
        <div className="user-selector-trigger">
          <div className="user-info">
            <div className="user-avatar">DU</div>
            <div className="user-details">
              <div className="user-name">Loading...</div>
              <div className="user-department">Please wait</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="user-selector">
      <button 
        type="button"
        className="user-selector-trigger"
        onClick={() => setIsOpen(!isOpen)}
        {...(isOpen ? { 'aria-expanded': true } : { 'aria-expanded': false })}
      >
        <div className="user-info">
          <div className="user-avatar">
            {selectedUser.name.split(' ').map(n => n[0]).join('')}
          </div>
          <div className="user-details">
            <div className="user-name">{selectedUser.name}</div>
            <div className="user-department">{selectedUser.department}</div>
          </div>
        </div>
        <div className={`dropdown-arrow ${isOpen ? 'open' : ''}`}>
          <svg 
            width="16" 
            height="16" 
            viewBox="0 0 16 16" 
            fill="currentColor"
          >
            <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="2" fill="none"/>
          </svg>
        </div>
      </button>

      {isOpen && (
        <>
          <div className="user-selector-overlay" onClick={() => setIsOpen(false)} />
          <div className="user-selector-dropdown">
            <div className="dropdown-header">
              <h3>Switch User</h3>
              <p>Select a user to view their tickets</p>
            </div>
            <div className="user-list">
              {DEMO_USERS.map((user) => (
                <button
                  key={user.id}
                  className={`user-option ${user.id === currentUser ? 'selected' : ''}`}
                  onClick={() => handleUserSelect(user.id)}
                >
                  <div className="user-avatar">
                    {user.name.split(' ').map(n => n[0]).join('')}
                  </div>
                  <div className="user-info">
                    <div className="user-name">{user.name}</div>
                    <div className="user-email">{user.email}</div>
                    <div className="user-department">{user.department}</div>
                  </div>
                  {user.id === currentUser && (
                    <div className="selected-indicator">✓</div>
                  )}
                </button>
              ))}
            </div>
            <div className="dropdown-footer">
              <p className="user-hint">
                Each user will only see tickets they've created
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}