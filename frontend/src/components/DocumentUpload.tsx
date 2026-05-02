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
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/documents/upload`, {
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
    <div className="card">
      <h3>Upload New Document</h3>
      {error && <p className="error">{error}</p>}
      <form onSubmit={handleUpload}>
        <input 
          id="file-upload"
          type="file" 
          accept=".pdf,.jpg,.jpeg,.png" 
          onChange={handleFileChange} 
          disabled={loading}
        />
        <button type="submit" disabled={!file || loading}>
          {loading ? 'Uploading...' : 'Upload'}
        </button>
      </form>
    </div>
  );
};

export default DocumentUpload;
