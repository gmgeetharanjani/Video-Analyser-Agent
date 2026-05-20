# Video Analyzer Frontend

React-based frontend application for the Video Analyzer Agent. Allows users to upload videos and interact with the AI agent through a chat interface.

## Features

- 📤 **Video Upload**: Drag-and-drop or file selection (up to 2GB)
- 📊 **Progress Tracking**: Real-time upload and processing status
- 💬 **Interactive Chat**: Ask questions about the video content
- 🎯 **Suggested Questions**: Quick-start prompts for common queries
- 📱 **Responsive Design**: Works on desktop and mobile devices
- ✨ **Modern UI**: Clean, intuitive interface with smooth animations

## Prerequisites

- Node.js 18+ and npm
- Video Analyzer Agent backend running (default: http://localhost:5000)

## Installation

```bash
# Install dependencies
npm install

# Start development server
npm start
```

The app will open at http://localhost:3000

## Build for Production

```bash
# Create optimized production build
npm run build

# The build folder contains the production-ready files
```

## Configuration

### Backend URL

The frontend is configured to proxy API requests to the backend. Update `package.json` if your backend runs on a different port:

```json
{
  "proxy": "http://localhost:5000"
}
```

For production, configure your web server to proxy `/upload-video`, `/health`, and `/.well-known/agent.json` to the backend.

## Usage

### 1. Upload Video

1. Click "Choose Video File" or drag and drop a video
2. Supported formats: MP4, AVI, MOV, MKV, WEBM
3. Maximum size: 2GB
4. Click "Process Video"
5. Wait for processing (frame extraction + transcription)

### 2. Ask Questions

Once processing is complete:

1. Use suggested questions or type your own
2. Press Enter or click "Send"
3. Get AI-powered answers based on video content
4. Continue the conversation with follow-up questions

### 3. Upload New Video

Click "Upload New Video" to analyze a different video

## Project Structure

```
video-frontend/
├── public/
│   └── index.html           # HTML template
├── src/
│   ├── components/
│   │   ├── VideoUpload.js   # Video upload component
│   │   ├── VideoUpload.css
│   │   ├── Chat.js          # Chat interface component
│   │   └── Chat.css
│   ├── App.js               # Main application component
│   ├── App.css
│   ├── index.js             # Application entry point
│   └── index.css
└── package.json
```

## Components

### VideoUpload

Handles video file selection, validation, and upload to the backend.

**Features:**
- File type validation
- Size validation (2GB limit)
- Upload progress tracking
- Error handling

### Chat

Interactive chat interface for asking questions about the video.

**Features:**
- Message history
- Suggested questions
- Typing indicators
- Auto-scroll to latest message
- Keyboard shortcuts (Enter to send)

## API Integration

The frontend communicates with the Video Analyzer Agent backend:

### Upload Video
```javascript
POST /upload-video
Content-Type: multipart/form-data
Body: FormData with video file
```

### Chat with Agent
```javascript
POST /.well-known/agent.json
Content-Type: application/json
Body: {
  message: {
    role: "user",
    parts: [{ text: "Your question" }]
  }
}
```

## Styling

The application uses a modern gradient theme with:
- Primary color: #667eea (purple-blue)
- Secondary color: #764ba2 (purple)
- Clean, card-based layout
- Smooth animations and transitions
- Responsive breakpoints for mobile

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Development

### Available Scripts

```bash
# Start development server
npm start

# Run tests
npm test

# Build for production
npm run build

# Eject from Create React App (irreversible)
npm run eject
```

### Environment Variables

Create a `.env` file for custom configuration:

```bash
REACT_APP_API_URL=http://localhost:5000
```

## Troubleshooting

### Backend Connection Issues

If the frontend can't connect to the backend:

1. Ensure the backend is running on port 5000
2. Check CORS configuration in backend
3. Verify proxy setting in package.json

### Upload Failures

If video uploads fail:

1. Check file size (must be < 2GB)
2. Verify file format is supported
3. Check backend logs for errors
4. Ensure sufficient disk space on backend

### Chat Not Working

If chat doesn't respond:

1. Verify video was processed successfully
2. Check browser console for errors
3. Ensure backend A2A endpoint is accessible
4. Check SAP AI Core credentials in backend

## License

Copyright © SAP SE