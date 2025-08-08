import React from 'react';
import './HomePage.css';

// Reuse the MedicalFeatureCards component
const MedicalFeatureCards = () => (
  <div className="medical-cards">
    <div className="medical-card">
      <div className="medical-gradient-glow"></div>
      <div className="medical-card-icon">🏥</div>
      <div className="medical-card-title">Health Policy Analysis</div>
      <div className="medical-card-desc">
        Get comprehensive analysis of your health insurance policies, coverage details, and benefits with our AI-powered medical assistant.
      </div>
      <div className="medical-card-action">
        Analyze Coverage →
      </div>
    </div>
    
    <div className="medical-card">
      <div className="medical-gradient-glow"></div>
      <div className="medical-card-icon">🛡️</div>
      <div className="medical-card-title">Claims Processing Support</div>
      <div className="medical-card-desc">
        Upload your medical documents and receive intelligent guidance on insurance claims, requirements, and approval processes.
      </div>
      <div className="medical-card-action">
        Process Claims →
      </div>
    </div>
    
    <div className="medical-card">
      <div className="medical-gradient-glow"></div>
      <div className="medical-card-icon">💬</div>
      <div className="medical-card-title">AI-Powered Consultation</div>
      <div className="medical-card-desc">
        Ask questions about your policies, coverage, or medical procedures using our advanced voice and text-based AI assistant.
      </div>
      <div className="medical-card-action">
        Start Consultation →
      </div>
    </div>
  </div>
);

const HomePage = ({ onGetStarted }) => {
  return (
    <div className="medical-main-app">
      {/* Medical Hero Section */}
      <section className="medical-hero-section">
        <div className="medical-hero-content">
          <h1 className="medical-title">
            Health & Insurance Policy RAG Companion Platform
          </h1>
          <div className="medical-subtitle">
            Your trusted healthcare assistant for insurance policies, claims, and medical guidance.<br />
            <span className="medical-highlight">AI-powered. Secure. Professional.</span>
          </div>
          <MedicalFeatureCards />
        </div>
      </section>

      {/* How It Works Section */}
      <section className="medical-how-it-works-section">
        <div className="container">
          <div className="medical-how-it-works-header">
            <h2 className="medical-how-it-works-title">How It Works</h2>
            <p className="medical-how-it-works-subtitle">
              Get started with our AI-powered healthcare assistant in just 3 simple steps
            </p>
          </div>
          
          <div className="medical-steps-container">
            <div className="medical-step">
              <div className="medical-step-circle">
                <div className="medical-step-number">1</div>
                <div className="medical-step-icon">📄</div>
              </div>
              <div className="medical-step-content">
                <h3 className="medical-step-title">Upload Documents</h3>
                <p className="medical-step-description">
                  Upload your health insurance policies, medical documents, or any healthcare-related files in PDF, TXT, or MD format.
                </p>
              </div>
              <div className="medical-step-connector"></div>
            </div>

            <div className="medical-step">
              <div className="medical-step-circle">
                <div className="medical-step-number">2</div>
                <div className="medical-step-icon">❓</div>
              </div>
              <div className="medical-step-content">
                <h3 className="medical-step-title">Ask Questions</h3>
                <p className="medical-step-description">
                  Ask specific questions about your policies, coverage, claims, or any healthcare procedures using text or voice input.
                </p>
              </div>
              <div className="medical-step-connector"></div>
            </div>

            <div className="medical-step">
              <div className="medical-step-circle">
                <div className="medical-step-number">3</div>
                <div className="medical-step-icon">🧠</div>
              </div>
              <div className="medical-step-content">
                <h3 className="medical-step-title">Get AI Insights</h3>
                <p className="medical-step-description">
                  Receive instant, accurate, and personalized insights powered by advanced AI that analyzes your documents and provides expert guidance.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Get Started CTA Section */}
      <section className="medical-cta-section">
        <div className="container">
          <div className="medical-cta-content">
            <h2 className="medical-cta-title">Ready to Get Started?</h2>
            <p className="medical-cta-subtitle">
              Join thousands of users who trust our AI-powered healthcare assistant for their insurance and medical needs.
            </p>
            <button 
              onClick={onGetStarted}
              className="medical-get-started-btn"
            >
              <span className="medical-get-started-icon">🚀</span>
              Get Started Now
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
