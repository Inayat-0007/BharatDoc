import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

interface Citation {
  page_number: number;
  chunk_index: number;
  text: string;
  similarity: number;
}

interface QueryResult {
  status: 'answered' | 'refused';
  answer: string | null;
  confidence: number;
  support_level: string | null;
  answer_mode: string | null;
  citations: Citation[];
  refusal_message: string | null;
  diagnostics: Record<string, any> | null;
}

interface Message {
  id: string;
  type: 'user' | 'assistant';
  text: string;
  confidence?: number;
  support_level?: string;
  answer_mode?: string;
  citations?: Citation[];
  refused?: boolean;
  timestamp: Date;
}

interface DocumentQAProps {
  documentId: number;
  documentName: string;
  onClose: () => void;
}

const DocumentQA: React.FC<DocumentQAProps> = ({ documentId, documentName, onClose }) => {
  const { token } = useAuth();
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [showDiagnostics, setShowDiagnostics] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      type: 'user',
      text: query.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentQuery = query.trim();
    setQuery('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/documents/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          query: currentQuery,
          document_id: documentId,
          top_k: 5
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `Request failed (${response.status})`);
      }

      const result: QueryResult = await response.json();

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        type: 'assistant',
        text: result.answer || result.refusal_message || 'No response',
        confidence: result.confidence,
        support_level: result.support_level || undefined,
        answer_mode: result.answer_mode || undefined,
        citations: result.citations,
        refused: result.status === 'refused',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        type: 'assistant',
        text: `Error: ${err.message}`,
        refused: true,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.8) return { label: 'High', className: 'badge-high' };
    if (confidence >= 0.5) return { label: 'Medium', className: 'badge-medium' };
    return { label: 'Low', className: 'badge-low' };
  };

  const getSupportBadge = (level: string) => {
    switch (level) {
      case 'supported': return { label: '✓ Verified', className: 'support-verified' };
      case 'partially_supported': return { label: '~ Partial', className: 'support-partial' };
      case 'unsupported': return { label: '✗ Unverified', className: 'support-unverified' };
      default: return { label: level, className: '' };
    }
  };

  return (
    <div className="qa-container">
      <div className="qa-header">
        <div className="qa-header-info">
          <button className="qa-back-btn" onClick={onClose} title="Back to documents">
            ← Back
          </button>
          <div className="qa-doc-name">
            <span className="qa-icon">📄</span>
            <h3>{documentName}</h3>
          </div>
        </div>
        <div className="qa-header-badge">
          <span className="qa-live-dot"></span>
          AI Q&A
        </div>
      </div>

      <div className="qa-messages">
        {messages.length === 0 && (
          <div className="qa-empty">
            <div className="qa-empty-icon">🔍</div>
            <h3>Ask a question about this document</h3>
            <p>BharatDoc will search through the document and provide answers with citations.</p>
            <div className="qa-suggestions">
              <button onClick={() => setQuery('What is this document about?')} className="qa-suggestion">
                What is this document about?
              </button>
              <button onClick={() => setQuery('Summarize the key points')} className="qa-suggestion">
                Summarize the key points
              </button>
            </div>
          </div>
        )}

        {messages.map(msg => (
          <div key={msg.id} className={`qa-message qa-message-${msg.type}`}>
            <div className="qa-message-avatar">
              {msg.type === 'user' ? '👤' : '🤖'}
            </div>
            <div className="qa-message-content">
              <div className={`qa-message-bubble ${msg.refused ? 'qa-refused' : ''}`}>
                <p className="qa-message-text">{msg.text}</p>
              </div>

              {msg.type === 'assistant' && !msg.refused && msg.confidence !== undefined && (
                <div className="qa-meta">
                  <span className={`qa-badge ${getConfidenceBadge(msg.confidence).className}`}>
                    {getConfidenceBadge(msg.confidence).label} confidence
                  </span>
                  {msg.support_level && (
                    <span className={`qa-badge ${getSupportBadge(msg.support_level).className}`}>
                      {getSupportBadge(msg.support_level).label}
                    </span>
                  )}
                  {msg.answer_mode && (
                    <span className="qa-badge badge-mode">
                      {msg.answer_mode === 'extractive' ? '📋 Extractive' : '🧠 Synthesized'}
                    </span>
                  )}
                </div>
              )}

              {msg.citations && msg.citations.length > 0 && (
                <div className="qa-citations">
                  <button
                    className="qa-citations-toggle"
                    onClick={() => setShowDiagnostics(showDiagnostics === msg.id ? null : msg.id)}
                  >
                    📑 {msg.citations.length} citation{msg.citations.length > 1 ? 's' : ''}
                    {showDiagnostics === msg.id ? ' ▲' : ' ▼'}
                  </button>
                  {showDiagnostics === msg.id && (
                    <div className="qa-citations-list">
                      {msg.citations.map((c, i) => (
                        <div key={i} className="qa-citation-item">
                          <div className="qa-citation-header">
                            <span className="qa-citation-page">Page {c.page_number}</span>
                            <span className="qa-citation-sim">
                              {(c.similarity * 100).toFixed(1)}% match
                            </span>
                          </div>
                          <p className="qa-citation-text">{c.text}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <span className="qa-timestamp">
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>
        ))}

        {loading && (
          <div className="qa-message qa-message-assistant">
            <div className="qa-message-avatar">🤖</div>
            <div className="qa-message-content">
              <div className="qa-message-bubble qa-typing">
                <span className="qa-dot"></span>
                <span className="qa-dot"></span>
                <span className="qa-dot"></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="qa-input-form" onSubmit={handleSubmit}>
        <div className="qa-input-wrapper">
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question about this document..."
            disabled={loading}
            className="qa-input"
            id="qa-query-input"
          />
          <button type="submit" disabled={loading || !query.trim()} className="qa-send-btn" id="qa-send-btn">
            {loading ? '...' : '→'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default DocumentQA;
