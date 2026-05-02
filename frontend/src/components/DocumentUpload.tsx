import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

const DocumentUpload = ({ onUploadSuccess }: { onUploadSuccess: () => void }) => {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { token } = useAuth();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || '/api';
      const response = await fetch(`${apiUrl}/documents/upload`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`
        },
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Upload failed');
      }

      setFile(null);
      onUploadSuccess();
      
      // Clear file input
      const fileInput = document.getElementById('file-upload') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
      
    } catch (err: any) {
      setError(err.message || 'Error uploading document');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
      <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
        <span className="w-8 h-8 rounded-lg bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center text-violet-600 dark:text-violet-400 text-sm">📄</span>
        Upload Document
      </h3>
      
      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm">
          {error}
        </div>
      )}
      
      <form onSubmit={handleUpload} className="flex flex-col sm:flex-row gap-3">
        <input
          id="file-upload"
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          onChange={handleFileChange}
          disabled={loading}
          className="flex-1 text-sm text-slate-600 dark:text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-violet-50 file:text-violet-700 dark:file:bg-violet-900/30 dark:file:text-violet-400 hover:file:bg-violet-100 dark:hover:file:bg-violet-900/50 file:cursor-pointer file:transition-colors"
        />
        <button
          type="submit"
          disabled={!file || loading}
          className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white font-semibold text-sm shadow-md shadow-violet-500/20 hover:shadow-violet-500/40 transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap"
        >
          {loading ? 'Uploading...' : 'Upload'}
        </button>
      </form>
    </div>
  );
};

export default DocumentUpload;
