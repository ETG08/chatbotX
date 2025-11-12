import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const messagesEndRef = useRef(null);

// Initialize session on component mount
  useEffect(() => {
    const storedSessionId = localStorage.getItem('sessionId');
    if (storedSessionId) {
      setSessionId(storedSessionId);
      loadHistory(storedSessionId);
    } else {
      const newSessionId = `session_${Date.now()}`;
      setSessionId(newSessionId);
      localStorage.setItem('sessionId', newSessionId);
    }
  }, []);

// Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

// Load conversation history from backend
  const loadHistory = async (sid) => {
    try {
      const response = await axios.get(`${API_URL}/api/history/${sid}`);
      if (response.data.history && response.data.history.length > 0) {
        setMessages(response.data.history.map(msg => ({
          text: msg.content,
          sender: msg.role === 'user' ? 'user' : 'ai',
          timestamp: new Date(msg.timestamp)
        })));
      }
    } catch (error) {
      console.error('Failed to load history:', error);
    }
  };

// Send message to backend
  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = {
      text: input,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_URL}/api/chat`, {
        message: currentInput,
        session_id: sessionId
      });

      const aiMessage = {
        text: response.data.response,
        sender: 'ai',
        timestamp: new Date(response.data.timestamp),
        toolsUsed: response.data.tools_used || []
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        text: 'Sorry, I encountered an error. Please try again.',
        sender: 'ai',
        timestamp: new Date(),
        isError: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

// Clear chat history
  const clearChat = async () => {
    if (window.confirm('Clear conversation history?')) {
      try {
        await axios.delete(`${API_URL}/api/session/${sessionId}`);
        setMessages([]);
        localStorage.removeItem('sessionId');
        const newSessionId = `session_${Date.now()}`;
        setSessionId(newSessionId);
        localStorage.setItem('sessionId', newSessionId);
      } catch (error) {
        console.error('Error clearing session:', error);
      }
    }
  };

// Handle Enter key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <h1>🏢 Company Assistant</h1>
          <p className="subtitle">Ask me anything about employees, policies, or leave balances</p>
        </div>
        <button onClick={clearChat} className="clear-btn">
          🗑️ Clear Chat
        </button>
      </header>

      <div className="chat-container">
        <div className="messages">
          {messages.length === 0 && (
            <div className="welcome">
              <h2>👋 Welcome to Company Assistant!</h2>
              <p>I can help you with:</p>
              <ul>
                <li>🔍 Finding employee information</li>
                <li>📅 Checking leave balances</li>
                <li>🎉 Company holidays and announcements</li>
                <li>🏢 Department information</li>
                <li>📋 Company policies</li>
              </ul>
              <p className="example">
                <strong>Try asking:</strong><br />
                "Who is John Doe?"<br />
                "What's the leave balance for EMP001?"<br />
                "Show me all departments"
              </p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.sender} ${msg.isError ? 'error' : ''}`}>
              <div className="message-content">
                <div className="message-header">
                  <span className="sender-icon">
                    {msg.sender === 'user' ? '👤' : '🤖'}
                  </span>
                  <span className="timestamp">
                    {msg.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                <div className="text">
                  {msg.sender === 'ai' ? (
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  ) : (
                    msg.text
                  )}
                </div>
                {msg.toolsUsed && msg.toolsUsed.length > 0 && (
                  <div className="tools-used">
                    <small>🔧 Used: {msg.toolsUsed.join(', ')}</small>
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="message ai">
              <div className="message-content">
                <div className="message-header">
                  <span className="sender-icon">🤖</span>
                  <span className="timestamp">Now</span>
                </div>
                <div className="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message... (Press Enter to send)"
            disabled={isLoading}
            className="message-input"
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            className="send-btn"
          >
            {isLoading ? '⏳' : '📤'} Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
