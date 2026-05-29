import { useState, useRef, useEffect } from "react";

const SESSION_ID = crypto.randomUUID();
const USER_ID = "demo_user_01";

function VenueCard({ venue, index, onSelect, disabled }) {
  const handleSelect = (e) => {
    e.stopPropagation();
    if (!disabled) onSelect(venue, index);
  };

  const popular = Array.isArray(venue.popular_items) ? venue.popular_items.filter(Boolean) : [];

  return (
    <div className="venue-card">
      <div className="venue-card-top">
        <div className="venue-card-title-block">
          <span className="venue-card-index">{index}</span>
          <div className="venue-card-title">
            <div className="venue-card-name">{venue.venue_name}</div>
            <div className="venue-card-meta">
              <span className="venue-card-cuisine">{venue.cuisine}</span>
              <span className="venue-card-dot">·</span>
              <span>~${venue.estimated_cost_per_person}/person</span>
              <span className="venue-card-dot">·</span>
              <span className="venue-card-rating">★ {venue.rating}</span>
            </div>
          </div>
        </div>
        <span className="venue-card-your-pick">Your pick</span>
      </div>
      {venue.description && (
        <p className="venue-card-description">{venue.description}</p>
      )}
      {popular.length > 0 && (
        <div className="venue-card-chips">
          {popular.slice(0, 3).map((item, i) => (
            <span key={i} className="venue-card-chip">{item}</span>
          ))}
        </div>
      )}
      <div className="venue-card-bottom">
        <span className="venue-card-address">{venue.address || ""}</span>
        <button
          type="button"
          className="venue-card-select"
          onClick={handleSelect}
          disabled={disabled}
        >
          Select
        </button>
      </div>
    </div>
  );
}

function ActionButtons({ actions, onAction, disabled }) {
  if (!actions || actions.length === 0) return null;
  return (
    <div className="action-row">
      {actions.map((a, i) => (
        <button
          key={i}
          type="button"
          className={`action-btn ${a.primary ? "action-btn-primary" : ""}`}
          onClick={() => onAction(a.message)}
          disabled={disabled}
        >
          {a.label}
        </button>
      ))}
    </div>
  );
}

/**
 * Split response text into the prose around the venue list.
 * The backend formats venue lines as "1. <name> — ..." — we drop those lines
 * (we render cards for them) and keep the header / footer prose.
 */
function splitVenueProse(text) {
  const lines = text.split("\n");
  const isVenueLine = (l) => /^\s*\d+\.\s+.+—/.test(l);
  let firstIdx = -1;
  let lastIdx = -1;
  lines.forEach((l, i) => {
    if (isVenueLine(l)) {
      if (firstIdx === -1) firstIdx = i;
      lastIdx = i;
    }
  });
  if (firstIdx === -1) return { before: text, after: "" };
  const before = lines.slice(0, firstIdx).join("\n").replace(/\n+$/, "");
  const after = lines.slice(lastIdx + 1).join("\n").replace(/^\n+/, "");
  return { before, after };
}

function Message({ msg, isLatest, sendText, loading }) {
  const isUser = msg.role === "user";
  const hasVenues = !isUser && Array.isArray(msg.venues) && msg.venues.length > 0;
  const hasActions = !isUser && isLatest && Array.isArray(msg.actions) && msg.actions.length > 0;
  const { before, after } = hasVenues ? splitVenueProse(msg.content) : { before: msg.content, after: "" };
  const interactive = isLatest && !loading;

  return (
    <div className={`message-row ${isUser ? "user-row" : "assistant-row"}`}>
      {!isUser && (
        <div className="avatar assistant-avatar">
          <span>AI</span>
        </div>
      )}
      <div className={`bubble ${isUser ? "user-bubble" : "assistant-bubble"}`}>
        {hasVenues ? (
          <>
            {before && <pre className="message-text">{before}</pre>}
            <div className="venue-list">
              {msg.venues.map((v, i) => (
                <VenueCard
                  key={`${v.venue_name}-${i}`}
                  venue={v}
                  index={i + 1}
                  onSelect={(_, idx) => sendText(String(idx))}
                  disabled={!interactive}
                />
              ))}
            </div>
            {after && <pre className="message-text">{after}</pre>}
          </>
        ) : (
          <pre className="message-text">{msg.content}</pre>
        )}
        {hasActions && <ActionButtons actions={msg.actions} onAction={sendText} disabled={!interactive} />}
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

  const sendText = async (text) => {
    if (!text || loading) return;
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: SESSION_ID, user_id: USER_ID, message: text }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "assistant", content: data.response, venues: data.venues, actions: data.actions }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Something went wrong. Please try again or visit OpenTable directly." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const sendInput = () => {
    const text = input.trim();
    if (!text) return;
    setInput("");
    sendText(text);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendInput();
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
            <Message
              key={i}
              msg={msg}
              isLatest={i === messages.length - 1}
              sendText={sendText}
              loading={loading}
            />
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
          <button className="send-btn" onClick={sendInput} disabled={!input.trim() || loading}>
            ↑
          </button>
        </div>
        <p className="disclaimer">ChatGPT can make mistakes. Confirm bookings before relying on them.</p>
      </footer>
    </div>
  );
}
