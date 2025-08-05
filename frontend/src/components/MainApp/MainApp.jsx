import React, { useState, useEffect } from 'react';
import { ragApi } from '../../api/ragApi';
import './MainApp.css';

const MainApp = () => {
  const [chatHistory, setChatHistory] = useState([]);
  const [query, setQuery] = useState('');
  const [ttsEnabled, setTtsEnabled] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [dbStats, setDbStats] = useState({ total_documents: 0 });
  const [isProcessing, setIsProcessing] = useState(false);

  const exampleQueries = [
    "What is covered under my insurance policy?",
    "46-year-old male, knee surgery in Pune",
    "What are the exclusions in my health policy?",
    "How to claim insurance for surgery?"
  ];

  const handleQuerySubmit = async (queryText) => {
    if (!queryText.trim()) return;
    
    setIsLoading(true);
    try {
      console.log('Sending query to backend:', queryText);
      
      const result = await ragApi.query(queryText, ttsEnabled);
      console.log('Backend response:', result);
      
      const isFromDocs = result.source_info.toLowerCase().includes('document');
      
      setChatHistory(prev => [...prev, {
        query: queryText,
        response: result.response,
        sourceInfo: result.source_info,
        isFromDocs,
        retrievedDocs: result.retrieved_documents || []
      }]);
      
      setQuery('');
    } catch (error) {
      console.error('Error processing query:', error);
      setChatHistory(prev => [...prev, {
        query: queryText,
        response: `Error: ${error.message}`,
        sourceInfo: 'Error',
        isFromDocs: false,
        retrievedDocs: []
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (files) => {
    setIsProcessing(true);
    
    for (const file of files) {
      try {
        console.log('Uploading file:', file.name);
        
        const result = await ragApi.uploadFile(file);
        console.log('Upload successful:', result);
        
        setUploadedFiles(prev => [...prev, {
          name: file.name,
          size: file.size,
          uploadTime: new Date().toISOString()
        }]);
        
        // Show success message
        setChatHistory(prev => [...prev, {
          query: `Uploaded: ${file.name}`,
          response: `✅ Successfully uploaded and processed "${file.name}". The document is now available for queries. Text length: ${result.text_length} characters.`,
          sourceInfo: 'System',
          isFromDocs: false,
          retrievedDocs: []
        }]);
        
      } catch (error) {
        console.error('Upload error:', error);
        setChatHistory(prev => [...prev, {
          query: `Upload error: ${file.name}`,
          response: `❌ Error uploading "${file.name}": ${error.message}`,
          sourceInfo: 'Error',
          isFromDocs: false,
          retrievedDocs: []
        }]);
      }
    }
    
    // Refresh stats after uploads
    await fetchDbStats();
    setIsProcessing(false);
  };

  const fetchDbStats = async () => {
    try {
      const stats = await ragApi.getStats();
      console.log('Stats fetched:', stats);
      setDbStats(stats);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const handleClearDatabase = async () => {
    if (window.confirm('Are you sure you want to clear all your documents from the database?')) {
      try {
        await ragApi.clearDatabase();
        setUploadedFiles([]);
        setChatHistory([]);
        await fetchDbStats();
        alert('Your documents cleared successfully');
      } catch (error) {
        console.error('Error clearing database:', error);
        alert('Error clearing database: ' + error.message);
      }
    }
  };

  useEffect(() => {
    fetchDbStats();
  }, []);

  return (
    <div className="main-app">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="hero-text">
            <h1 className="hero-title">
              <span className="gradient-text">Your Personal</span>
              <br />
              AI Document Assistant
            </h1>
            <p className="hero-subtitle">
              Upload your documents and get intelligent answers powered by AI. 
              Your personal knowledge base with advanced text-to-speech capabilities.
            </p>
            <div className="hero-stats">
              <div className="stat-item">
                <span className="stat-number">{dbStats.total_documents || 0}</span>
                <span className="stat-label">Your Documents</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">{dbStats.tts_available ? 'ON' : 'OFF'}</span>
                <span className="stat-label">Text-to-Speech</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">24/7</span>
                <span className="stat-label">AI Support</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* RAG Interface Section */}
      <section className="rag-section">
        <div className="container">
          <div className="rag-container">
            {/* Enhanced Sidebar */}
            <div className="sidebar">
              {/* System Status Card */}
              <div className="status-card">
                <div className="status-header">
                  <div className="status-indicator">
                    <span className="status-dot"></span>
                    <span className="status-text">System Ready</span>
                  </div>
                  <div className="db-stats-badge">
                    <span className="stats-number">{dbStats.total_documents || 0}</span>
                    <span className="stats-label">Documents</span>
                  </div>
                </div>
              </div>

              {/* Upload Card */}
              <div className="upload-card">
                <div className="card-header">
                  <h3 className="card-title">
                    <span className="card-icon">📄</span>
                    Upload Documents
                  </h3>
                </div>
                <div className="card-content">
                  <div className="upload-info">
                    <p><strong>Supported formats:</strong></p>
                    <div className="format-tags">
                      <span className="format-tag">PDF</span>
                      <span className="format-tag">TXT</span>
                      <span className="format-tag">MD</span>
                    </div>
                  </div>
                  
                  <div className="upload-area">
                    <input
                      type="file"
                      multiple
                      accept=".pdf,.md,.txt,.markdown"
                      onChange={(e) => handleFileUpload(Array.from(e.target.files))}
                      className="file-input"
                      id="file-upload"
                      disabled={isProcessing}
                    />
                    <label htmlFor="file-upload" className="upload-label">
                      <div className="upload-icon">📁</div>
                      <div className="upload-text">
                        <span>{isProcessing ? 'Processing...' : 'Drop files here or'}</span>
                        <span className="upload-link">browse</span>
                      </div>
                    </label>
                  </div>

                  {uploadedFiles.length > 0 && (
                    <div className="uploaded-files">
                      <h4>Recent uploads:</h4>
                      <ul>
                        {uploadedFiles.slice(-3).map((file, index) => (
                          <li key={index}>✓ {file.name}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              {/* Settings Card */}
              <div className="settings-card">
                <div className="card-header">
                  <h3 className="card-title">
                    <span className="card-icon">⚙️</span>
                    Settings
                  </h3>
                </div>
                <div className="card-content">
                  <div className="setting-item">
                    <label className="toggle-switch">
                      <input
                        type="checkbox"
                        checked={ttsEnabled}
                        onChange={(e) => setTtsEnabled(e.target.checked)}
                      />
                      <span className="toggle-slider"></span>
                    </label>
                    <div className="setting-info">
                      <span className="setting-label">Text-to-Speech</span>
                      <span className="setting-desc">Enable voice responses</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Actions Card */}
              <div className="actions-card">
                <div className="card-header">
                  <h3 className="card-title">
                    <span className="card-icon">🔧</span>
                    Quick Actions
                  </h3>
                </div>
                <div className="card-content">
                  <div className="action-buttons">
                    <button 
                      onClick={fetchDbStats} 
                      className="action-btn primary"
                      disabled={isProcessing}
                    >
                      <span className="btn-icon">🔄</span>
                      Refresh Stats
                    </button>
                    <button 
                      onClick={() => setChatHistory([])}
                      className="action-btn secondary"
                    >
                      <span className="btn-icon">🗑️</span>
                      Clear Chat
                    </button>
                    <button 
                      onClick={handleClearDatabase}
                      className="action-btn danger"
                    >
                      <span className="btn-icon">💾</span>
                      Clear My Documents
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Enhanced Main Content */}
            <div className="main-content">
              <div className="chat-container">
                <div className="chat-messages">
                  {chatHistory.length === 0 ? (
                    <div className="welcome-section">
                      <div className="welcome-content">
                        <div className="welcome-icon">💡</div>
                        <h3 className="welcome-title">Get Started with AI Assistant</h3>
                        <p className="welcome-text">
                          Try these example queries or upload documents to begin exploring
                        </p>
                        
                        <div className="example-queries">
                          {exampleQueries.map((example, index) => (
                            <button
                              key={index}
                              onClick={() => handleQuerySubmit(example)}
                              className="example-query-btn"
                              disabled={isLoading}
                            >
                              <span className="query-icon">💬</span>
                              <span className="query-text">{example}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="chat-history">
                      {chatHistory.map((chat, index) => (
                        <div key={index} className="chat-exchange">
                          <div className="user-message">
                            <div className="message-avatar">
                              <span>👤</span>
                            </div>
                            <div className="message-bubble user">
                              <div className="message-content">{chat.query}</div>
                            </div>
                          </div>
                          
                          <div className="assistant-message">
                            <div className="message-avatar">
                              <span>🤖</span>
                            </div>
                            <div className="message-bubble assistant">
                              <div className="message-content">{chat.response}</div>
                              <div className={`source-badge ${chat.isFromDocs ? 'from-docs' : 'from-llm'}`}>
                                <span className="source-icon">
                                  {chat.isFromDocs ? '📄' : '🧠'}
                                </span>
                                <span className="source-text">{chat.sourceInfo}</span>
                              </div>
                              {chat.retrievedDocs && chat.retrievedDocs.length > 0 && (
                                <div className="retrieved-docs-info">
                                  <small>Retrieved from {chat.retrievedDocs.length} document(s)</small>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {isLoading && (
                    <div className="loading-section">
                      <div className="loading-animation">
                        <div className="loading-spinner"></div>
                        <div className="loading-dots">
                          <span></span>
                          <span></span>
                          <span></span>
                        </div>
                      </div>
                      <p className="loading-text">AI is processing your query...</p>
                    </div>
                  )}
                </div>

                {/* Enhanced Query Input */}
                <div className="query-input-section">
                  <form 
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleQuerySubmit(query);
                    }}
                    className="query-form"
                  >
                    <div className="input-wrapper">
                      <div className="input-container">
                        <input
                          type="text"
                          value={query}
                          onChange={(e) => setQuery(e.target.value)}
                          placeholder="Ask anything about your documents..."
                          className="query-input"
                          disabled={isLoading}
                        />
                        <button 
                          type="submit" 
                          className="send-button"
                          disabled={isLoading || !query.trim()}
                        >
                          {isLoading ? (
                            <div className="btn-loading">
                              <div className="btn-spinner"></div>
                            </div>
                          ) : (
                            <>
                              <span>Send</span>
                              <span className="send-icon">🚀</span>
                            </>
                          )}
                        </button>
                      </div>
                      <div className="input-suggestions">
                        <span className="suggestion-label">Suggestions:</span>
                        <div className="suggestion-chips">
                          <button 
                            type="button"
                            onClick={() => setQuery("What is covered under my policy?")}
                            className="suggestion-chip"
                          >
                            Coverage details
                          </button>
                          <button 
                            type="button"
                            onClick={() => setQuery("How to file a claim?")}
                            className="suggestion-chip"
                          >
                            Filing claims
                          </button>
                          <button 
                            type="button"
                            onClick={() => setQuery("What are the exclusions?")}
                            className="suggestion-chip"
                          >
                            Policy exclusions
                          </button>
                        </div>
                      </div>
                    </div>
                  </form>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default MainApp;