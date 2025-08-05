// ...existing code...

      {/* RAG Interface Section */}
      <section id="rag-interface" className={`rag-section ${showRAGInterface ? 'active' : ''}`}>
        <div className="container">
          <div className="rag-header">
            <h2 className="rag-title">🤖 AI Document Assistant</h2>
            <p className="rag-subtitle">
              Upload your documents and start asking questions to get instant AI-powered insights
            </p>
          </div>

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
                    <span className="stats-number">{dbStats.total_documents}</span>
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
                    />
                    <label htmlFor="file-upload" className="upload-label">
                      <div className="upload-icon">📁</div>
                      <div className="upload-text">
                        <span>Drop files here or</span>
                        <span className="upload-link">browse</span>
                      </div>
                    </label>
                  </div>

                  {uploadedFiles.length > 0 && (
                    <div className="uploaded-files">
                      <h4>Recent uploads:</h4>
                      <ul>
                        {uploadedFiles.slice(-3).map((file, index) => (
                          <li key={index}>✓ {file}</li>
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
                    <button onClick={fetchDbStats} className="action-btn primary">
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
                    <button className="action-btn danger">
                      <span className="btn-icon">💾</span>
                      Clear Database
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
// ...existing code...