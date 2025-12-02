"use client";

import { useEffect, useState, useRef } from "react";
import { updateTicketStatus } from "@/lib/api";

interface SlackChannel {
  channel_id: string;
  channel_name: string;
  incident_id: string;
  webhook_url: string;
  message_count: number;
  last_activity: string;
}

interface SlackIntegrationProps {
  incidentId: string;
  ticketId: string;
  onChannelReady?: (channel: SlackChannel) => void;
  onIncidentResolved?: () => void;
}

export default function SlackIntegration({ incidentId, ticketId, onChannelReady, onIncidentResolved }: SlackIntegrationProps) {
  const [channel, setChannel] = useState<SlackChannel | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [resolving, setResolving] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const mountedRef = useRef(false);
  const initializedRef = useRef(false);

  // Debug: Log when messages change
  useEffect(() => {
    console.log('🔄 Messages state changed:', messages.length, 'messages');
    console.log('📝 Messages:', messages.map(m => `${m.user}: ${m.message.substring(0, 30)}`));
  }, [messages]);

  // Auto-scroll to bottom when messages change (only within the messages container)
  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    // Only run once - prevent re-initialization
    if (initializedRef.current) return;
    initializedRef.current = true;

    // Fetch Slack channel info and initial messages
    const fetchSlackChannel = async () => {
      try {
        setLoading(true);
        
        // Mock Slack channel data - in real implementation, this would come from your API
        const mockChannel: SlackChannel = {
          channel_id: "C07V57P5N31",
          channel_name: `p1-${incidentId.toLowerCase()}`,
          incident_id: incidentId,
          webhook_url: "",  // Set via environment variable in backend
          message_count: 0,
          last_activity: new Date().toISOString()
        };
        
        setChannel(mockChannel);
        if (onChannelReady) {
          onChannelReady(mockChannel);
        }
        
        // Fetch actual messages from backend
        const response = await fetch(`http://localhost:8000/api/incidents/${incidentId}/messages`, {
          headers: {
            'X-User-Id': localStorage.getItem('selectedUserId') || 'demo-user'
          }
        });

        if (response.ok) {
          const data = await response.json();
          if (data.messages && data.messages.length > 0) {
            const loadedMessages = data.messages.map((msg: any) => ({
              id: msg.id || msg.message_id,
              user: msg.user || msg.user_name || 'Operations Team',
              avatar: msg.type === 'operations' ? '👨‍💻' : '👤',
              message: msg.message || msg.message_text,
              timestamp: msg.timestamp || msg.created_at,
              type: msg.type || 'user'
            }));
            setMessages(loadedMessages);
          }
        }
        
        setLoading(false);
        
      } catch (err) {
        setError("Failed to load Slack channel");
        setLoading(false);
      }
    };

    if (incidentId) {
      fetchSlackChannel();
    }
  }, [incidentId, onChannelReady]);

  // Poll for incident status and new messages from Slack (operations team replies)
  useEffect(() => {
    if (!incidentId) return;

    const pollMessages = async () => {
      try {
        console.log('🔄 Polling messages for incident:', incidentId);
        
        // First, try to sync messages from Slack (pulls from Slack API)
        try {
          const syncResponse = await fetch(`http://localhost:8000/api/incidents/${incidentId}/sync-slack-messages`, {
            method: 'POST',
            headers: {
              'X-User-Id': localStorage.getItem('selectedUserId') || 'demo-user'
            }
          });
          
          if (syncResponse.ok) {
            const syncData = await syncResponse.json();
            if (syncData.synced > 0) {
              console.log(`✅ Synced ${syncData.synced} messages from Slack`);
            }
          }
        } catch (syncError) {
          console.log('⚠️ Slack sync not available (need bot token)');
        }
        
        // Then fetch all messages from database
        const response = await fetch(`http://localhost:8000/api/incidents/${incidentId}/messages`, {
          headers: {
            'X-User-Id': localStorage.getItem('selectedUserId') || 'demo-user'
          }
        });

        console.log('📡 Poll response status:', response.status);

        if (response.ok) {
          const data = await response.json();
          console.log('📦 Received data:', data);
          console.log('📬 Messages from server:', data.messages?.length || 0);
          
          if (data.messages && data.messages.length > 0) {
            console.log('📋 All server messages:', data.messages);
            
            // Update messages with server data, avoiding duplicates
            setMessages(prevMessages => {
              console.log('Current messages in state:', prevMessages.length);
              
              const existingIds = new Set(prevMessages.map(m => m.id));
              console.log('Existing message IDs:', Array.from(existingIds));
              
              const newMessages = data.messages
                .filter((msg: any) => !existingIds.has(msg.id))
                .map((msg: any) => ({
                  id: msg.id || msg.message_id,
                  user: msg.user || msg.user_name || 'Operations Team',
                  avatar: msg.type === 'operations' ? '👨‍💻' : '👤',
                  message: msg.message || msg.message_text,
                  timestamp: msg.timestamp || msg.created_at,
                  type: msg.type || 'user'
                }));
              
              console.log('🔍 New messages to add:', newMessages.length);
              console.log('📝 New message details:', JSON.stringify(newMessages, null, 2));
              if (newMessages.length > 0) {
                console.log('📥 Adding new messages:', newMessages);
                return [...prevMessages, ...newMessages];
              }
              return prevMessages;
            });
          } else {
            console.log('ℹ️ No messages from server yet');
          }
        } else {
          console.error('❌ Poll failed with status:', response.status);
        }
      } catch (error) {
        console.error('❌ Failed to poll messages:', error);
      }
    };

    // Poll every 5 seconds
    console.log('⏰ Setting up message polling (every 5 seconds)');
    const interval = setInterval(pollMessages, 5000);
    
    // Initial poll
    pollMessages();

    return () => {
      console.log('🛑 Stopping message polling');
      clearInterval(interval);
    };
  }, [incidentId]);

  // Poll for incident status changes (check if resolved)
  useEffect(() => {
    if (!incidentId) return;

    const pollIncidentStatus = async () => {
      try {
        const response = await fetch(`http://localhost:8000/p1-incidents/by-incident/${incidentId}`, {
          headers: {
            'X-User-Id': localStorage.getItem('selectedUserId') || 'demo-user'
          }
        });

        if (response.ok) {
          const data = await response.json();
          
          // Check if incident was resolved
          if (data.incident?.status === 'resolved' && !resolving) {
            console.log('🎯 Incident has been resolved by operations team!');
            setResolving(true);
            onIncidentResolved?.();
          }
        }
      } catch (error) {
        console.error('❌ Failed to poll incident status:', error);
      }
    };

    // Poll every 3 seconds
    const interval = setInterval(pollIncidentStatus, 3000);
    
    // Initial poll
    pollIncidentStatus();

    return () => {
      clearInterval(interval);
    };
  }, [incidentId, resolving, onIncidentResolved]);

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim()) return;
    
    const messageText = newMessage.trim();
    const now = Date.now();
    const messageId = `msg-${now}-${Math.random().toString(36).substr(2, 9)}`;
    
    console.log('=== SENDING MESSAGE ===');
    console.log('Text:', messageText);
    console.log('Current messages count:', messages.length);
    
    const message = {
      id: messageId,
      user: "You",
      avatar: "👤",
      message: messageText,
      timestamp: new Date().toISOString(),
      type: "outbound"
    };
    
    // Clear input immediately for better UX
    setNewMessage("");
    
    // Add user's message to UI immediately
    setMessages(prevMessages => {
      const updatedMessages = [...prevMessages, message];
      console.log('New messages count:', updatedMessages.length);
      console.log('Last message:', updatedMessages[updatedMessages.length - 1]);
      return updatedMessages;
    });
    
    // Force a re-render by logging
    setTimeout(() => {
      console.log('Messages after update:', messages.length);
    }, 100);
    
    try {
      // Send to real Slack via backend API
      const response = await fetch(`http://localhost:8000/api/incidents/${incidentId}/send-message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageText,
          user_name: 'User'
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to send message');
      }
      
      console.log('✅ Message sent to real Slack channel');
      
      // Check if user typed "resolved" to auto-resolve the incident
      if (messageText.toLowerCase() === 'resolved') {
        console.log('🎯 Auto-resolving incident based on user message');
        await handleResolveIncident();
      }
      
    } catch (error) {
      console.error('Failed to send message:', error);
      
      // Add error message only if send fails
      const errorMessage = {
        id: `msg-error-${Date.now()}`,
        user: "System",
        avatar: "❌",
        message: "Failed to send to Slack. Please try again.",
        timestamp: new Date().toISOString(),
        type: "system"
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleResolveIncident = async () => {
    if (resolving) return;
    
    setResolving(true);
    
    try {
      // Update ticket status to resolved
      await updateTicketStatus(ticketId, {
        status: "resolved",
        resolution_note: "P1 incident resolved via Slack communication channel"
      });
      
      // Add resolution message to chat
      const resolutionMessage = {
        id: String(messages.length + 1),
        user: "System",
        avatar: "✅",
        message: "🎉 P1 Incident has been marked as RESOLVED. Ticket status updated to 'resolved'.",
        timestamp: new Date().toISOString(),
        type: "system"
      };
      
      setMessages([...messages, resolutionMessage]);
      
      // Notify parent component
      onIncidentResolved?.();
      
    } catch (error) {
      console.error("Failed to resolve incident:", error);
      
      const errorMessage = {
        id: String(messages.length + 1),
        user: "System",
        avatar: "❌",
        message: "Failed to resolve incident. Please try again or contact support.",
        timestamp: new Date().toISOString(),
        type: "system"
      };
      
      setMessages([...messages, errorMessage]);
    } finally {
      setResolving(false);
    }
  };

  if (loading) {
    return (
      <div className="slack-integration loading">
        <div className="slack-header">
          <div className="slack-icon">💬</div>
          <h3>Setting up Slack Channel...</h3>
        </div>
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Creating dedicated P1 incident channel</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="slack-integration error">
        <div className="slack-header">
          <div className="slack-icon">⚠️</div>
          <h3>Slack Integration Error</h3>
        </div>
        <p className="error-text">{error}</p>
        <button className="retry-btn" onClick={() => window.location.reload()}>
          Retry Connection
        </button>
      </div>
    );
  }

  return (
    <div className="slack-integration active">
      <div className="slack-header">
        <div className="slack-info">
          <div className="slack-icon">💬</div>
          <div className="channel-details">
            <h3>Live Incident Channel</h3>
            <p className="channel-name">#{channel?.channel_name}</p>
          </div>
        </div>
        <div className="slack-status">
          <div className="status-indicator online"></div>
          <span>3 Ops Team Online</span>
        </div>
      </div>

      <div className="slack-messages">
        <div className="messages-header">
          <span>Real-time Communication</span>
          <span className="message-count">{messages.length} messages (Debug: {JSON.stringify(messages.length)})</span>
        </div>
        
        <div className="messages-container" ref={messagesContainerRef}>
          {messages.length === 0 && <div className="empty-messages">No messages yet</div>}
          {messages.map((message, index) => (
            <div key={message.id} className={`message ${message.type}`}>
              <div className="message-avatar">{message.avatar}</div>
              <div className="message-content">
                <div className="message-header">
                  <span className="message-user">{message.user}</span>
                  <span className="message-time">{formatTime(message.timestamp)}</span>
                </div>
                <div className="message-text">{message.message}</div>
              </div>
            </div>
          ))}
        </div>
        
        <div className="slack-input">
          <input 
            type="text" 
            placeholder="Type a message to the operations team..."
            className="message-input"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
          />
          <button className="send-btn" onClick={handleSendMessage}>Send</button>
        </div>
        
        {/* Incident Resolution Section */}
        <div className="incident-resolution">
          <div className="resolution-header">
            <span className="icon">✅</span>
            <span>Incident Resolution</span>
          </div>
          <div className="resolution-actions">
            <button 
              className="resolve-btn"
              onClick={handleResolveIncident}
              disabled={resolving}
            >
              {resolving ? "Resolving..." : "Mark as Resolved"}
            </button>
            <p className="resolution-note">
              This will close the P1 incident and update the ticket status to resolved.
            </p>
          </div>
        </div>
      </div>

      <div className="slack-footer">
        <div className="escalation-info">
          <div className="escalation-item">
            <span className="icon">📞</span>
            <span>24/7 Hotline: +1 (555) 911-P1P1</span>
          </div>
          <div className="escalation-item">
            <span className="icon">⚡</span>
            <span>Critical Incidents: p1@yourfault.com</span>
          </div>
        </div>
        
        <button className="open-slack-btn">
          Open Full Slack Channel
        </button>
      </div>
    </div>
  );
}