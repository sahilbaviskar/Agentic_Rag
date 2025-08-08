import React, { useState } from 'react';
import Login from './Login';
import Signup from './Signup';

const AuthPage = ({ onBack }) => {
  const [isLogin, setIsLogin] = useState(true);

  return (
    <div style={{ position: 'relative' }}>
      {onBack && (
        <button 
          onClick={onBack}
          style={{
            position: 'absolute',
            top: '20px',
            left: '20px',
            background: 'rgba(255, 255, 255, 0.1)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            color: 'white',
            fontSize: '1rem',
            padding: '8px 16px',
            borderRadius: '8px',
            cursor: 'pointer',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'all 0.3s ease'
          }}
          onMouseEnter={(e) => {
            e.target.style.background = 'rgba(255, 255, 255, 0.2)';
          }}
          onMouseLeave={(e) => {
            e.target.style.background = 'rgba(255, 255, 255, 0.1)';
          }}
        >
          ← Back to Home
        </button>
      )}
      
      {isLogin ? (
        <Login onSwitchToSignup={() => setIsLogin(false)} />
      ) : (
        <Signup onSwitchToLogin={() => setIsLogin(true)} />
      )}
    </div>
  );
};

export default AuthPage;