import React, { useState } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import AuthPage from './components/Auth/AuthPage';
import Header from './components/Header/Header';
import HomePage from './components/HomePage/HomePage';
import MainApp from './components/MainApp/MainApp';
import './App.css';

const AppContent = () => {
  const { user, loading } = useAuth();
  const [showAuth, setShowAuth] = useState(false);

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // Show auth page if user clicked "Get Started" but isn't authenticated
  if (showAuth && !user) {
    return <AuthPage onBack={() => setShowAuth(false)} />;
  }

  // Show RAG functionality if user is authenticated
  if (user) {
    return (
      <div className="app">
        <Header showUserInfo={true} />
        <MainApp />
      </div>
    );
  }

  // Show homepage by default
  return (
    <div className="app">
      <Header showUserInfo={false} />
      <HomePage onGetStarted={() => setShowAuth(true)} />
    </div>
  );
};

const App = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;