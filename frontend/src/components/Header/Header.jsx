import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import './Header.css';

const Header = ({ showUserInfo = true }) => {
  const { user, logout } = useAuth();
  const [showDropdown, setShowDropdown] = useState(false);

  const handleLogout = () => {
    logout();
    setShowDropdown(false);
  };

  return (
    <header className="app-header">
      <div className="header-content">
        <div className="header-left">
          <h1 className="app-title">
            <i className="fas fa-brain"></i>
            Health & Insurance RAG
          </h1>
          <span className="app-subtitle">Intelligent Healthcare Assistant</span>
        </div>
        
        {showUserInfo && user && (
          <div className="header-right">
            <div className="user-menu">
              <button 
                className="user-button"
                onClick={() => setShowDropdown(!showDropdown)}
              >
                <div className="user-avatar">
                  <i className="fas fa-user"></i>
                </div>
                <div className="user-info">
                  <span className="user-name">{user?.name}</span>
                  <span className="user-email">{user?.email}</span>
                </div>
                <i className={`fas fa-chevron-down dropdown-icon ${showDropdown ? 'open' : ''}`}></i>
              </button>
              
              {showDropdown && (
                <div className="user-dropdown">
                  <div className="dropdown-header">
                    <div className="user-avatar-large">
                      <i className="fas fa-user"></i>
                    </div>
                    <div>
                      <div className="dropdown-name">{user?.name}</div>
                      <div className="dropdown-email">{user?.email}</div>
                    </div>
                  </div>
                  
                  <div className="dropdown-divider"></div>
                  
                  <button className="dropdown-item" onClick={handleLogout}>
                    <i className="fas fa-sign-out-alt"></i>
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
      
      {showDropdown && (
        <div 
          className="dropdown-overlay" 
          onClick={() => setShowDropdown(false)}
        ></div>
      )}
    </header>
  );
};

export default Header;