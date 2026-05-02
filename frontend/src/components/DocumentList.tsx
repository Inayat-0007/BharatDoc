import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';

interface Document {
  id: number;
  filename: string;
  status: string;
  created_at: string;
}

interface DocumentListProps {
  refreshTrigger: number;
  onQueryDocument?: (docId: number, docName: string) => void;
}

const statusConfig: Record<string, { bg: string; text: string; dot: string }> = {
  uploaded: { bg: 'bg-blue-50 dark:bg-blue-900/20', text: 'text-blue-700 dark:text-blue-400', dot: 'bg-blue-500' },
  processing: { bg: 'bg-amber-50 dark:bg-amber-900/20', text: 'text-amber-700 dark:text-amber-400', dot: 'bg-amber-500' },
  ready: { bg: 'bg-emerald-50 dark:bg-emerald-900/20', text: 'text-emerald-700 dark:text-emerald-400', dot: 'bg-emerald-500' },
  failed: { bg: 'bg-red-50 dark:bg-red-900/20', text: 'text-red-700 dark:text-red-400', dot: 'bg-red-500' },
};

const DocumentList: React.FC<DocumentListProps> = ({ refreshTrigger, onQueryDocument }) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { token } = useAuth();

  const fetchDocuments = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || '/api';
      const response = await fetch(`${apiUrl}/documents`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      if (!response.ok) throw new Error('Failed to fetch documents');
      const data = await response.json();
      setDocuments(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchDocuments();
    }
  }, [token, refreshTrigger]);

  // Polling logic for documents still processing
  useEffect(() => {
    if (!token) return;
    
    const hasProcessingDocs = documents.some(d => d.status === 'uploaded' || d.status === 'processing');
    if (!hasProcessingDocs) return;

    const intervalId = setInterval(() => {
      fetchDocuments();
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(intervalId);
  }, [documents, token]);

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this document?")) return;
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || '/api';
      const response = await fetch(`${apiUrl}/documents/${id}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      
      if (!response.ok) throw new Error('Failed to delete document');
      
      setDocuments(docs => docs.filter(doc => doc.id !== id));
    } catch (err: any) {
      alert(err.message);
    }
  };

  if (loading && documents.length === 0) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-8 text-center">
        <div className="animate-shimmer h-4 w-48 mx-auto rounded-lg"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm">
        {error}
      </div>
    );
  }
  
  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
      <div className="p-6 border-b border-slate-100 dark:border-slate-700">
        <h3 className="text-base font-semibold text-slate-900 dark:text-white flex items-center gap-2">
          <span className="w-8 h-8 rounded-lg bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center text-violet-600 dark:text-violet-400 text-sm">📁</span>
          Your Documents
          {documents.length > 0 && (
            <span className="ml-auto text-xs font-medium text-slate-400 bg-slate-100 dark:bg-slate-700 px-2.5 py-1 rounded-full">
              {documents.length}
            </span>
          )}
        </h3>
      </div>

      {documents.length === 0 ? (
        <div className="p-12 text-center">
          <div className="text-4xl mb-3 opacity-40">📄</div>
          <p className="text-sm text-slate-500 dark:text-slate-400">No documents uploaded yet.</p>
        </div>
      ) : (
        <ul className="divide-y divide-slate-100 dark:divide-slate-700">
          {documents.map(doc => {
            const status = statusConfig[doc.status] || statusConfig.uploaded;
            return (
              <li key={doc.id} className="flex items-center justify-between px-6 py-4 hover:bg-slate-50 dark:hover:bg-slate-750 transition-colors animate-fade-in-up">
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-slate-100 dark:bg-slate-700 flex items-center justify-center text-slate-500 text-sm">
                    {doc.filename.endsWith('.pdf') ? '📕' : '🖼️'}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                      {doc.filename}
                    </p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${status.bg} ${status.text}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${status.dot} ${doc.status === 'processing' ? 'animate-pulse-dot' : ''}`}></span>
                    {doc.status}
                  </span>
                </div>
                <div className="flex items-center gap-2 ml-4 flex-shrink-0">
                  {doc.status === 'ready' && onQueryDocument && (
                    <button
                      id={`qa-btn-${doc.id}`}
                      onClick={() => onQueryDocument(doc.id, doc.filename)}
                      className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white text-xs font-semibold shadow-md shadow-violet-500/20 hover:shadow-violet-500/40 transition-all duration-200 hover:-translate-y-0.5"
                    >
                      🔍 Ask AI
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="p-2 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                    title="Delete document"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
};

export default DocumentList;
