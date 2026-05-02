import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import DocumentUpload from '../components/DocumentUpload';
import DocumentList from '../components/DocumentList';
import DocumentQA from '../components/DocumentQA';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [activeQA, setActiveQA] = useState<{ id: number; name: string } | null>(null);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  
  const handleUploadSuccess = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  const handleQueryDocument = (docId: number, docName: string) => {
    setActiveQA({ id: docId, name: docName });
  };

  const handleCloseQA = () => {
    setActiveQA(null);
  };

  // Show Q&A view when a document is selected
  if (activeQA) {
    return (
      <div className="dashboard-container dashboard-qa">
        <DocumentQA
          documentId={activeQA.id}
          documentName={activeQA.name}
          onClose={handleCloseQA}
        />
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <header className="app-header">
        <h1>BharatDoc Dashboard</h1>
        <button onClick={handleLogout}>Logout</button>
      </header>
      <main className="dashboard-main">
        <div className="card welcome-card">
          <h2>Welcome, {user?.email}</h2>
        </div>
        
        <DocumentUpload onUploadSuccess={handleUploadSuccess} />
        <DocumentList 
          refreshTrigger={refreshTrigger} 
          onQueryDocument={handleQueryDocument}
        />
      </main>
    </div>
  );
};

export default Dashboard;
