import React, { useState } from 'react';
import axios from 'axios';
import './VideoUpload.css';

function VideoUpload({ onVideoProcessed, onProcessingStart, onProcessingError, isProcessing }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    setError('');
    
    if (file) {
      // Validate file size (2GB limit)
      const maxSize = 2 * 1024 * 1024 * 1024; // 2GB in bytes
      if (file.size > maxSize) {
        setError(`File too large. Maximum size is 2GB. Your file is ${(file.size / (1024**3)).toFixed(2)}GB`);
        setSelectedFile(null);
        return;
      }

      // Validate file type
      const validTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm'];
      if (!validTypes.includes(file.type) && !file.name.match(/\.(mp4|avi|mov|mkv|webm)$/i)) {
        setError('Invalid file type. Please upload a video file (MP4, AVI, MOV, MKV, or WEBM)');
        setSelectedFile(null);
        return;
      }

      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a video file first');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      setError('');
      onProcessingStart();
      setUploadProgress(0);

      const response = await axios.post('/upload-video', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(percentCompleted);
        },
      });

      if (response.data.status === 'success') {
        onVideoProcessed(response.data.metadata);
      } else {
        setError('Failed to process video');
      }
    } catch (err) {
      console.error('Upload error:', err);
      setError(
        err.response?.data?.detail || 
        'Failed to upload and process video. Please try again.'
      );
      setUploadProgress(0);
      // Reset processing state
      if (onProcessingError) {
        onProcessingError();
      }
    }
  };

  return (
    <div className="video-upload">
      <div className="upload-card">
        <h2>Upload Video</h2>
        <p className="upload-description">
          Select a video file (up to 2GB) to analyze. The agent will extract frames,
          transcribe audio, and prepare to answer your questions.
        </p>

        <div className="file-input-wrapper">
          <input
            type="file"
            id="video-file"
            accept="video/*"
            onChange={handleFileSelect}
            disabled={isProcessing}
            className="file-input"
          />
          <label htmlFor="video-file" className="file-label">
            {selectedFile ? selectedFile.name : 'Choose Video File'}
          </label>
        </div>

        {selectedFile && !isProcessing && (
          <div className="file-info">
            <p>📁 <strong>Selected:</strong> {selectedFile.name}</p>
            <p>📊 <strong>Size:</strong> {(selectedFile.size / (1024**2)).toFixed(2)} MB</p>
          </div>
        )}

        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        {uploadProgress > 0 && uploadProgress < 100 && (
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${uploadProgress}%` }}>
              {uploadProgress}%
            </div>
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={!selectedFile || isProcessing}
          className="upload-button"
        >
          {isProcessing ? 'Processing...' : 'Process Video'}
        </button>

        <div className="supported-formats">
          <p><strong>Supported formats:</strong> MP4, AVI, MOV, MKV, WEBM</p>
          <p><strong>Max size:</strong> 2GB</p>
        </div>
      </div>
    </div>
  );
}

export default VideoUpload;