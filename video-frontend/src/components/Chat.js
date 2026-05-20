import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './Chat.css';

function Chat({ videoMetadata }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `Hello! I've analyzed your video "${videoMetadata.filename}". I can answer questions about its content, summarize it, explain concepts, or teach you what's covered in the video. What would you like to know?`
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const suggestedQuestions = [
    'Summarize this video',
    'What are the main concepts explained?',
    'Teach me the key topics from this video',
    'What happens in the first minute?',
    'List the important points covered'
  ];

  const handleSend = async (question = input) => {
    if (!question.trim()) return;

    const userMessage = { role: 'user', content: question };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post('/chat', {
        message: question,
        context_id: 'default'
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.data.response || 'Sorry, I could not process your request.'
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        role: 'assistant',
        content: `❌ Sorry, there was an error processing your question: ${error.response?.data?.detail || error.message || 'Unknown error'}`
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestionClick = (question) => {
    handleSend(question);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h3>💬 Ask Questions About Your Video</h3>
        <p className="chat-subtitle">
          The agent will answer based only on the video content
        </p>
      </div>

      <div className="messages-container">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.role}`}>
            <div className="message-avatar">
              {message.role === 'user' ? '👤' : '🤖'}
            </div>
            <div className="message-content">
              <div className="message-text">{message.content}</div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {messages.length === 1 && (
        <div className="suggested-questions">
          <p className="suggestions-title">💡 Try asking:</p>
          <div className="suggestions-grid">
            {suggestedQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(question)}
                className="suggestion-button"
                disabled={isLoading}
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="chat-input-container">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask a question about the video..."
          disabled={isLoading}
          className="chat-input"
          rows="3"
        />
        <button
          onClick={() => handleSend()}
          disabled={!input.trim() || isLoading}
          className="send-button"
        >
          {isLoading ? '⏳' : '📤'} Send
        </button>
      </div>

      <div className="chat-info">
        <p>
          ℹ️ The agent is grounded to the video content and will only answer
          questions based on what's shown and said in the video.
        </p>
      </div>
    </div>
  );
}

export default Chat;