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

const DocumentList: React.FC<DocumentListProps> = ({ refreshTrigger, onQueryDocument }) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { token } = useAuth();

  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/documents`, {
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
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/documents/${id}`, {
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

  if (loading && documents.length === 0) return <p>Loading documents...</p>;
  if (error) return <p className="error">{error}</p>;
  
  return (
    <div className="card">
      <h3>Your Documents</h3>
      {documents.length === 0 ? (
        <p>No documents uploaded yet.</p>
      ) : (
        <ul className="document-list">
          {documents.map(doc => (
            <li key={doc.id} className="document-item">
              <div className="doc-info">
                <strong>{doc.filename}</strong>
                <span className={`status badge-${doc.status}`}>{doc.status}</span>
                <span className="date">{new Date(doc.created_at).toLocaleDateString()}</span>
              </div>
              <div className="doc-actions">
                {doc.status === 'ready' && onQueryDocument && (
                  <button
                    className="btn-query"
                    onClick={() => onQueryDocument(doc.id, doc.filename)}
                    id={`qa-btn-${doc.id}`}
                  >
                    🔍 Ask AI
                  </button>
                )}
                <button className="btn-delete" onClick={() => handleDelete(doc.id)}>Delete</button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default DocumentList;
