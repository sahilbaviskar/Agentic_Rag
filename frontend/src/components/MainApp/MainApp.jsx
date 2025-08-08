import React, { useState, useEffect, useRef } from 'react';
import { ragApi } from '../../api/ragApi';
import './MainApp.css';
import './MedicalTheme.css'; 

const MainApp = () => {
  const [chatHistory, setChatHistory] = useState([]);
  const [query, setQuery] = useState('');
  const [ttsEnabled, setTtsEnabled] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [dbStats, setDbStats] = useState({ total_documents: 0 });
  const [isProcessing, setIsProcessing] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);

  const exampleQueries = [
    "What is covered under my health insurance policy?",
    "How do I file a claim for medical expenses?",
    "What are the exclusions in my insurance policy?",
    "What is the process for pre-authorization of surgery?",
    "How much is my co-payment for specialist visits?",
    "What documents are needed for claim processing?"
  ];

  // Text-to-Speech for answers (toggle start/stop)
  const [speakingIndex, setSpeakingIndex] = useState(null);
  const speakText = (text, index) => {
    if ('speechSynthesis' in window) {
      if (window.speechSynthesis.speaking && speakingIndex === index) {
        window.speechSynthesis.cancel();
        setSpeakingIndex(null);
        return;
      }
      window.speechSynthesis.cancel(); // Stop any current speech
      const utterance = new window.SpeechSynthesisUtterance(text);
      utterance.rate = 1;
      utterance.pitch = 1;
      utterance.lang = 'en-US';
      utterance.onend = () => setSpeakingIndex(null);
      utterance.onerror = () => setSpeakingIndex(null);
      setSpeakingIndex(index);
      window.speechSynthesis.speak(utterance);
    } else {
      alert('Text-to-Speech is not supported in this browser.');
    }
  };

  // Enhanced Speech-to-Text for input with better error handling and user feedback
  const startListening = () => {
    // Check if browser supports speech recognition
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      setQuery('Speech recognition not supported. Please type your question.');
      setTimeout(() => setQuery(''), 3000);
      return;
    }

    try {
      // Clean up any existing recognition
      if (recognitionRef.current) {
        recognitionRef.current.stop();
        recognitionRef.current = null;
      }

      // Create new recognition instance
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();

      // Simple, reliable configuration
      recognition.continuous = false;  // Single phrase
      recognition.interimResults = false;  // Only final results
      recognition.lang = 'en-US';
      recognition.maxAlternatives = 1;

      let hasStarted = false;
      let finalTranscript = '';

      recognition.onstart = () => {
        hasStarted = true;
        setIsListening(true);
        setQuery('🎤 Listening... Speak now!');
        console.log('Speech recognition started');
      };

      recognition.onresult = (event) => {
        console.log('Speech result received:', event.results);
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          if (result.isFinal) {
            finalTranscript += result[0].transcript;
          }
        }

        if (finalTranscript.trim()) {
          setQuery(finalTranscript.trim());
          console.log('Final transcript:', finalTranscript);
        }
      };

      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        
        if (event.error === 'no-speech') {
          setQuery('No speech heard. Try again.');
        } else if (event.error === 'not-allowed') {
          setQuery('Microphone access denied. Please allow microphone access.');
        } else {
          setQuery('Speech recognition error. Please try again.');
        }
        
        setTimeout(() => {
          if (!finalTranscript.trim()) {
            setQuery('');
          }
        }, 2000);
      };

      recognition.onend = () => {
        setIsListening(false);
        console.log('Speech recognition ended');
        
        if (!finalTranscript.trim() && hasStarted) {
          setQuery('No speech detected. Please try again.');
          setTimeout(() => setQuery(''), 2000);
        }
      };

      // Store reference and start
      recognitionRef.current = recognition;
      recognition.start();

    } catch (error) {
      console.error('Failed to start speech recognition:', error);
      setIsListening(false);
      setQuery('Failed to start speech recognition. Please try again.');
      setTimeout(() => setQuery(''), 2000);
    }
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  };

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
    <div className="medical-main-app">
      {/* Enhanced RAG Section - Only this section now */}
      <section className="medical-rag-section">
        <div className="container">
          <div className="medical-rag-header">
            <h2 className="medical-rag-title">🏥 Healthcare AI Assistant</h2>
            <p className="medical-rag-subtitle">
              Upload your medical documents and get instant AI-powered insights and guidance
            </p>
          </div>

          <div className="medical-rag-container">
            {/* Enhanced Sidebar */}
            <div className="medical-sidebar">
              {/* System Status Card */}
              <div className="medical-status-card">
                <div className="medical-card-header">
                  <div className="medical-status-indicator">
                    <span className="medical-status-dot"></span>
                    <span className="medical-status-text">System Ready</span>
                  </div>
                  <div className="medical-stats-badge">
                    <span className="medical-stats-number">{dbStats.total_documents}</span>
                    <span className="medical-stats-label">Documents</span>
                  </div>
                </div>
              </div>

              {/* Upload Card */}
              <div className="medical-upload-card">
                <div className="medical-card-header">
                  <h3 className="medical-card-title">
                    <span className="medical-card-icon">📄</span>
                    Upload Medical Documents
                  </h3>
                </div>
                <div className="medical-card-content">
                  <div className="medical-upload-info">
                    <p><strong>Supported formats:</strong></p>
                    <div className="medical-format-tags">
                      <span className="medical-format-tag">PDF</span>
                      <span className="medical-format-tag">TXT</span>
                      <span className="medical-format-tag">MD</span>
                    </div>
                  </div>
                  
                  <div className="medical-upload-area">
                    <input
                      type="file"
                      multiple
                      accept=".pdf,.md,.txt,.markdown"
                      onChange={(e) => handleFileUpload(Array.from(e.target.files))}
                      className="medical-file-input"
                      id="medical-file-upload"
                    />
                    <label htmlFor="medical-file-upload" className="medical-upload-label">
                      <div className="medical-upload-icon">🏥</div>
                      <div className="medical-upload-text">
                        <span>Drop medical files here or</span>
                        <span className="medical-upload-link">browse</span>
                      </div>
                    </label>
                  </div>

                  {uploadedFiles.length > 0 && (
                    <div className="medical-uploaded-files">
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

              

              {/* Actions Card */}
              <div className="medical-actions-card">
                <div className="medical-card-header">
                  <h3 className="medical-card-title">
                    <span className="medical-card-icon">🔧</span>
                    Quick Actions
                  </h3>
                </div>
                <div className="medical-card-content">
                  <div className="medical-action-buttons">
                    <button onClick={fetchDbStats} className="medical-action-btn primary">
                      <span className="medical-btn-icon">🔄</span>
                      Refresh Stats
                    </button>
                    <button 
                      onClick={() => setChatHistory([])}
                      className="medical-action-btn secondary"
                    >
                      <span className="medical-btn-icon">🗑️</span>
                      Clear Chat
                    </button>
                    <button 
                      onClick={handleClearDatabase}
                      className="medical-action-btn danger"
                      disabled={isProcessing || dbStats.total_documents === 0}
                      title="Clear all your uploaded documents from the database"
                    >
                      <span className="medical-btn-icon">🗂️</span>
                      Clear My Documents
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Enhanced Main Content */}
            <div className="medical-main-content">
              {chatHistory.length === 0 ? (
                <>
                  {/* Compact Welcome Section */}
                  <div className="medical-chat-messages">
                    <div className="medical-welcome-section">
                      <div className="medical-welcome-content">
                        <div className="medical-welcome-header">
                          <div className="medical-welcome-icon">🏥</div>
                          <h3 className="medical-welcome-title">Welcome to Your Healthcare AI Assistant</h3>
                          <p className="medical-welcome-text">
                            Get started by asking questions about your health insurance, policies, or upload medical documents for instant AI-powered insights.
                          </p>
                        </div>
                        
                        {/* Compact CTA Section */}
                        <div className="medical-welcome-cta">
                          <p className="medical-welcome-cta-text">Ready to get started?</p>
                          <div className="medical-welcome-cta-buttons">
                            <button 
                              onClick={() => document.getElementById('medical-file-upload').click()}
                              className="medical-welcome-cta-btn primary"
                            >
                              <span className="medical-welcome-cta-icon">📄</span>
                              Upload Documents
                            </button>
                            <button 
                              onClick={() => document.querySelector('.medical-query-input').focus()}
                              className="medical-welcome-cta-btn secondary"
                            >
                              <span className="medical-welcome-cta-icon">💬</span>
                              Ask a Question
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Main Content Sections - Examples and Tips */}
                  <div className="medical-main-content-sections">
                    {/* Example Queries Section */}
                    <div className="medical-content-section">
                      <h4 className="medical-content-section-title">
                        <span className="medical-content-section-icon">💬</span>
                        Try these example questions:
                      </h4>
                      <div className="medical-main-example-queries">
                        {exampleQueries.map((example, index) => (
                          <button
                            key={index}
                            onClick={() => handleQuerySubmit(example)}
                            className="medical-main-example-query-btn"
                            disabled={isLoading}
                          >
                            <span className="medical-main-query-icon">❓</span>
                            <span className="medical-main-query-text">{example}</span>
                            <span className="medical-main-query-arrow">→</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="medical-chat-container">
                  <div className="medical-chat-messages">
                    <div className="medical-chat-history">
                      {chatHistory.map((chat, index) => (
                        <div key={index} className="medical-chat-exchange">
                          <div className="medical-user-message">
                            <div className="medical-message-avatar">
                              <span>👤</span>
                            </div>
                            <div className="medical-message-bubble user">
                              <div className="medical-message-content">{chat.query}</div>
                            </div>
                          </div>
                          
                          <div className="medical-assistant-message">
                            <div className="medical-message-avatar">
                              <span>🏥</span>
                            </div>
                            <div className="medical-message-bubble assistant">
                              <div className="medical-message-content">{chat.response}</div>
                              <div className={`medical-source-badge ${chat.isFromDocs ? 'from-docs' : 'from-llm'}`}>
                                <span className="medical-source-icon">
                                  {chat.isFromDocs ? '📄' : '🧠'}
                                </span>
                                <span className="medical-source-text">{chat.sourceInfo}</span>
                              </div>
                              <button
                                onClick={() => speakText(chat.response, index)}
                                className={`medical-tts-btn ${speakingIndex === index ? 'speaking' : ''}`}
                                title="Listen to response"
                              >
                                <span>{speakingIndex === index ? '🔇' : '🔊'}</span>
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                    
                    {isLoading && (
                      <div className="medical-loading-section">
                        <div className="medical-loading-animation">
                          <div className="medical-loading-spinner"></div>
                          <div className="medical-loading-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                          </div>
                        </div>
                        <p className="medical-loading-text">Analyzing your healthcare query...</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Query Input Section - Always visible */}
              <div className="medical-query-input-section">
                <form 
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleQuerySubmit(query);
                  }}
                  className="medical-query-form"
                >
                  <div className="medical-input-wrapper">
                    <div className="medical-input-container">
                      <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Ask about your health insurance, medical procedures, or policies..."
                        className={`medical-query-input ${isListening ? 'listening' : ''}`}
                        disabled={isLoading}
                      />
                      <button
                        type="button"
                        className={`medical-mic-button ${isListening ? 'listening' : ''}`}
                        onClick={startListening}
                        title="Speak your question"
                        disabled={isLoading}
                      >
                        <span role="img" aria-label="mic">🎤</span>
                        {isListening && <div className="medical-speech-indicator"></div>}
                      </button>
                      <button 
                        type="submit" 
                        className="medical-send-button"
                        disabled={isLoading || !query.trim()}
                      >
                        {isLoading ? (
                          <div className="medical-btn-loading">
                            <div className="medical-btn-spinner"></div>
                          </div>
                        ) : (
                          <>
                            <span>Send</span>
                            <span className="medical-send-icon">🚀</span>
                          </>
                        )}
                      </button>
                    </div>
                    <div className="medical-input-suggestions">
                      <span className="medical-suggestion-label">Suggestions:</span>
                      <div className="medical-suggestion-chips">
                        <button 
                          type="button"
                          onClick={() => setQuery("What is covered under my policy?")}
                          className="medical-suggestion-chip"
                        >
                          Coverage details
                        </button>
                        <button 
                          type="button"
                          onClick={() => setQuery("How to file a claim?")}
                          className="medical-suggestion-chip"
                        >
                          Filing claims
                        </button>
                        <button 
                          type="button"
                          onClick={() => setQuery("What are the exclusions?")}
                          className="medical-suggestion-chip"
                        >
                          Policy exclusions
                        </button>
                      </div>
                    </div>
                  </div>
                </form>
                {isListening && (
                  <div className="medical-stt-status">🎤 Listening... Speak now!</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default MainApp;