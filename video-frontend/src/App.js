import React, { useState } from 'react';
import './App.css';
import VideoUpload from './components/VideoUpload';
import Chat from './components/Chat';

function App() {
  const [videoProcessed, setVideoProcessed] = useState(false);
  const [videoMetadata, setVideoMetadata] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleVideoProcessed = (metadata) => {
    setVideoMetadata(metadata);
    setVideoProcessed(true);
    setIsProcessing(false);
  };

  const handleProcessingStart = () => {
    setIsProcessing(true);
  };

  const handleProcessingError = () => {
    setIsProcessing(false);
  };

  const handleReset = () => {
    setVideoProcessed(false);
    setVideoMetadata(null);
    setIsProcessing(false);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎬 Video Analyzer Agent</h1>
        <p>Upload a video and ask questions about its content</p>
      </header>

      <main className="App-main">
        {!videoProcessed ? (
          <div className="upload-section">
            <VideoUpload 
              onVideoProcessed={handleVideoProcessed}
              onProcessingStart={handleProcessingStart}
              onProcessingError={handleProcessingError}
              isProcessing={isProcessing}
            />
            {isProcessing && (
              <div className="processing-indicator">
                <div className="spinner"></div>
                <p>Processing video... This may take a few minutes.</p>
                <p className="processing-note">
                  Extracting frames, transcribing audio, and analyzing content...
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="chat-section">
            <div className="video-info">
              <h3>✅ Video Processed Successfully</h3>
              <div className="metadata">
                <p><strong>Filename:</strong> {videoMetadata.filename}</p>
                <p><strong>Duration:</strong> {videoMetadata.duration_seconds}s</p>
                <p><strong>Resolution:</strong> {videoMetadata.width}x{videoMetadata.height}</p>
                <p><strong>Size:</strong> {videoMetadata.size_mb} MB</p>
              </div>
              <button onClick={handleReset} className="reset-button">
                Upload New Video
              </button>
            </div>
            <Chat videoMetadata={videoMetadata} />
          </div>
        )}
      </main>

      <footer className="App-footer">
        <p>Powered by SAP Application Foundation & PydanticAI</p>
      </footer>
    </div>
  );
}

export default App;