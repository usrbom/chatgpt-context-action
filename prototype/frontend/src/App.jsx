import { useState, useRef, useEffect } from "react";

const SESSION_ID = crypto.randomUUID();
const USER_ID = "demo_user_01";

function Message({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div className={`message-row ${isUser ? "user-row" : "assistant-row"}`}>
      {!isUser && (
        <div className="avatar assistant-avatar">
          <span>AI</span>
        </div>
      )}
      <div className={`bubble ${isUser ? "user-bubble" : "assistant-bubble"}`}>
        <pre className="message-text">{msg.content}</pre>
      </div>
      {isUser && (
        <div className="avatar user-avatar">
          <span>U</span>
        </div>
      )}
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="message-row assistant-row">
      <div className="avatar assistant-avatar">
        <span>AI</span>
      </div>
      <div className="bubble assistant-bubble typing-bubble">
        <span className="dot" />
        <span className="dot" />
        <span className="dot" />
      </div>
    </div>
  );
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleReset = async () => {
    await fetch("/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: SESSION_ID }),
    });
    setMessages([]);
  };

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: SESSION_ID, user_id: USER_ID, message: text }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "assistant", content: data.response }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Something went wrong. Please try again or visit OpenTable directly." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-title">ChatGPT</div>
        <button className="reset-btn" onClick={handleReset}>
          New chat
        </button>
      </header>

      <main className="chat-area">
        <div className="messages">
          {messages.map((msg, i) => (
            <Message key={i} msg={msg} />
          ))}
          {loading && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>
      </main>

      <footer className="input-area">
        <div className="input-box">
          <textarea
            className="input-field"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message ChatGPT"
            rows={1}
            disabled={loading}
          />
          <button className="send-btn" onClick={sendMessage} disabled={!input.trim() || loading}>
            ↑
          </button>
        </div>
        <p className="disclaimer">ChatGPT can make mistakes. Confirm bookings before relying on them.</p>
      </footer>
    </div>
  );
}
