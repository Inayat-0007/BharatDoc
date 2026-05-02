import { useState } from 'react';
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
      <div className="h-screen max-w-4xl mx-auto">
        <DocumentQA
          documentId={activeQA.id}
          documentName={activeQA.name}
          onClose={handleCloseQA}
        />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
      {/* Header */}
      <header className="flex items-center justify-between mb-8 pb-6 border-b border-slate-200 dark:border-slate-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-700 flex items-center justify-center shadow-md shadow-violet-500/20">
            <span className="text-white font-bold text-sm">B</span>
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white">BharatDoc</h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">Dashboard</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg transition-colors"
        >
          Logout
        </button>
      </header>

      {/* Welcome */}
      <div className="bg-gradient-to-r from-violet-50 to-purple-50 dark:from-violet-900/20 dark:to-purple-900/20 rounded-2xl p-6 mb-6 border border-violet-100 dark:border-violet-800/30">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
          Welcome back, <span className="text-violet-600 dark:text-violet-400">{user?.email}</span>
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Upload documents and ask AI-powered questions with citation-backed answers.
        </p>
      </div>

      {/* Upload + List */}
      <div className="space-y-6">
        <DocumentUpload onUploadSuccess={handleUploadSuccess} />
        <DocumentList 
          refreshTrigger={refreshTrigger} 
          onQueryDocument={handleQueryDocument}
        />
      </div>
    </div>
  );
};

export default Dashboard;
