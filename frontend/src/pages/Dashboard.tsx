import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import DocumentUpload from '../components/DocumentUpload';
import DocumentList from '../components/DocumentList';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  
  const handleUploadSuccess = () => {
    setRefreshTrigger(prev => prev + 1);
  };

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
        <DocumentList refreshTrigger={refreshTrigger} />
      </main>
    </div>
  );
};

export default Dashboard;
