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
  const [mode, setMode] = useState<'audit' | 'summary'>('audit');
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
      const apiUrl = import.meta.env.VITE_API_URL || '/api';
      const response = await fetch(`${apiUrl}/documents/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          query: currentQuery,
          document_id: documentId,
          top_k: mode === 'summary' ? 10 : 5,
          mode: mode
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
    if (confidence >= 0.8) return { label: 'High', className: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400' };
    if (confidence >= 0.5) return { label: 'Medium', className: 'bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400' };
    return { label: 'Low', className: 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400' };
  };

  const getSupportBadge = (level: string) => {
    switch (level) {
      case 'supported': return { label: '✓ Verified', className: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400' };
      case 'partially_supported': return { label: '~ Partial', className: 'bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400' };
      case 'unsupported': return { label: '✗ Unverified', className: 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400' };
      default: return { label: level, className: 'bg-slate-50 text-slate-700 dark:bg-slate-700 dark:text-slate-300' };
    }
  };

  return (
    <div className="flex flex-col h-screen bg-white dark:bg-slate-900">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <button
            onClick={onClose}
            title="Back to documents"
            className="p-2 rounded-lg text-slate-500 hover:text-violet-600 hover:bg-violet-50 dark:hover:bg-violet-900/20 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
          </button>
          <div className="flex items-center gap-2">
            <span className="text-lg">📄</span>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white truncate max-w-[200px] sm:max-w-none">
              {documentName}
            </h3>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs font-semibold text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-900/20 px-3 py-1.5 rounded-full">
          <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse-dot"></span>
          AI Q&A
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 space-y-5">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="text-5xl mb-4 opacity-50">🔍</div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
              Ask a question about this document
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-sm mb-6">
              BharatDoc will search through the document and provide answers with citations.
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              <button
                onClick={() => setQuery('What is this document about?')}
                className="px-4 py-2 text-xs font-medium text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-full hover:border-violet-300 hover:text-violet-600 dark:hover:border-violet-700 dark:hover:text-violet-400 transition-colors"
              >
                What is this document about?
              </button>
              <button
                onClick={() => setQuery('Summarize the key points')}
                className="px-4 py-2 text-xs font-medium text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-full hover:border-violet-300 hover:text-violet-600 dark:hover:border-violet-700 dark:hover:text-violet-400 transition-colors"
              >
                Summarize the key points
              </button>
            </div>
          </div>
        )}

        {messages.map(msg => (
          <div key={msg.id} className={`flex gap-3 animate-fade-in-up ${msg.type === 'user' ? 'flex-row-reverse' : ''}`}>
            {/* Avatar */}
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center text-sm">
              {msg.type === 'user' ? '👤' : '🤖'}
            </div>

            {/* Content */}
            <div className={`max-w-[75%] flex flex-col gap-1.5 ${msg.type === 'user' ? 'items-end' : 'items-start'}`}>
              {/* Bubble */}
              <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                msg.type === 'user'
                  ? 'bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-br-sm'
                  : msg.refused
                    ? 'bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800/40 text-slate-800 dark:text-slate-200 rounded-bl-sm'
                    : 'bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 rounded-bl-sm'
              }`}>
                <p className="whitespace-pre-wrap break-words">{msg.text}</p>
              </div>

              {/* Meta badges */}
              {msg.type === 'assistant' && !msg.refused && msg.confidence !== undefined && (
                <div className="flex flex-wrap gap-1.5">
                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${getConfidenceBadge(msg.confidence).className}`}>
                    {getConfidenceBadge(msg.confidence).label} confidence
                  </span>
                  {msg.support_level && (
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${getSupportBadge(msg.support_level).className}`}>
                      {getSupportBadge(msg.support_level).label}
                    </span>
                  )}
                  {msg.answer_mode && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-violet-50 text-violet-700 dark:bg-violet-900/20 dark:text-violet-400">
                      {msg.answer_mode === 'extractive' ? '📋 Extractive' : '🧠 Synthesized'}
                    </span>
                  )}
                </div>
              )}

              {/* Citations */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-1">
                  <button
                    onClick={() => setShowDiagnostics(showDiagnostics === msg.id ? null : msg.id)}
                    className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:border-violet-300 hover:text-violet-600 dark:hover:border-violet-700 dark:hover:text-violet-400 transition-colors"
                  >
                    📑 {msg.citations.length} citation{msg.citations.length > 1 ? 's' : ''}
                    <svg className={`w-3 h-3 transition-transform ${showDiagnostics === msg.id ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                  </button>
                  {showDiagnostics === msg.id && (
                    <div className="mt-2 space-y-2 animate-fade-in-up">
                      {msg.citations.map((c, i) => (
                        <div key={i} className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-3">
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="text-[11px] font-semibold text-violet-600 dark:text-violet-400">
                              Page {c.page_number}
                            </span>
                            <span className="text-[10px] text-slate-400 bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded">
                              {(c.similarity * 100).toFixed(1)}% match
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">{c.text}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Timestamp */}
              <span className="text-[10px] text-slate-400 opacity-70">
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {loading && (
          <div className="flex gap-3 animate-fade-in-up">
            <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center text-sm">🤖</div>
            <div className="px-4 py-3 rounded-2xl rounded-bl-sm bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center gap-1.5">
              <span className="qa-dot"></span>
              <span className="qa-dot"></span>
              <span className="qa-dot"></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-4 sm:px-6 py-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
        {/* Mode selector */}
        <div className="flex justify-center mb-3">
          <div className="inline-flex bg-white dark:bg-slate-800 p-1 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm gap-1">
            <button
              type="button"
              onClick={() => setMode('summary')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center gap-1.5 ${
                mode === 'summary'
                  ? 'bg-violet-600 text-white shadow-md shadow-violet-500/25'
                  : 'text-slate-500 dark:text-slate-400 hover:bg-violet-50 dark:hover:bg-violet-900/20 hover:text-violet-600 dark:hover:text-violet-400'
              }`}
            >
              🧠 Quick Summary
            </button>
            <button
              type="button"
              onClick={() => setMode('audit')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center gap-1.5 ${
                mode === 'audit'
                  ? 'bg-violet-600 text-white shadow-md shadow-violet-500/25'
                  : 'text-slate-500 dark:text-slate-400 hover:bg-violet-50 dark:hover:bg-violet-900/20 hover:text-violet-600 dark:hover:text-violet-400'
              }`}
            >
              🛡️ Strict Audit
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            ref={inputRef}
            id="qa-query-input"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={mode === 'summary' ? "Ask for a summary or overview..." : "Ask a specific factual question..."}
            disabled={loading}
            className="flex-1 px-4 py-3 rounded-xl border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
          />
          <button
            id="qa-send-btn"
            type="submit"
            disabled={loading || !query.trim()}
            className="w-12 h-12 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white flex items-center justify-center shadow-md shadow-violet-500/25 hover:shadow-violet-500/40 transition-all duration-200 hover:scale-105 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100 flex-shrink-0"
          >
            {loading ? (
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path></svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default DocumentQA;
