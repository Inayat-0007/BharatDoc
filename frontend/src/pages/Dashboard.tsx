import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="dashboard-container">
      <header className="app-header">
        <h1>BharatDoc Dashboard</h1>
        <button onClick={handleLogout}>Logout</button>
      </header>
      <main>
        <div className="card">
          <h2>Welcome, {user?.email}</h2>
          <p>This is your protected dashboard.</p>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
