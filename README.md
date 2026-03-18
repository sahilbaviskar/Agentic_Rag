# 🤖 Agentic RAG System

A full-stack Retrieve-and-Generate (RAG) system with a React frontend, a Python Flask backend, Groq LLM integration, and robust fallback mechanisms to ensure high availability. 

This application allows users to upload documents (PDF and text files), which are processed and stored securely. Users can then ask intelligent queries about their uploaded documents using an AI assistant powered by Groq and Llama 3 models.

---

## ✨ Key Features

- **User Authentication:** Secure signup and login system utilizing JWT tokens and password hashing.
- **Document Management:** Upload, process, and store personal documents securely and isolated per-user.
- **Agentic AI Responses:** Natural language document-based question answering using Groq API (Llama-3.3-70b-versatile). 
- **Graceful Degradation:** A robust fallback system that continues to operate and perform basic keyword-based document retrieval even if the AI or database services are temporarily unavailable.
- **Dual Database Architecture:** 
  - *Primary:* MongoDB with Vector Search capabilities
  - *Fallback:* SQLite local storage for maximum resilience 

## 🛠️ Tech Stack

### Frontend
- **Framework:** React / React Scripts
- **Styling:** CSS
- **Network:** Axios

### Backend
- **Framework:** Flask, Flask-CORS
- **AI/LLM:** Groq API `llama-3.3-70b-versatile`
- **Embeddings:** `sentence-transformers`
- **Database:** MongoDB (via `pymongo`) & SQLite
- **Security:** `bcrypt`, `PyJWT`
- **Utilities:** `python-dotenv`, `PyPDF2`

---

## 🚀 Setup Instructions

### 1. Prerequisites
- Node.js & npm (for the frontend)
- Python 3.8+ (for the backend)
- A [Groq Console](https://console.groq.com/) API Key.

### 2. Backend Setup

Open a terminal and navigate to the backend directory:
```bash
cd backend
```

Install the required Python dependencies:
```bash
pip install -r requirements_enhanced.txt
```

Create a `.env` file in the `backend` directory with the following variables:
```env
# Essential
GROQ_API_KEY=gsk_your_groq_api_key_here
JWT_SECRET=your-secure-production-secret-key 

# Database 
MONGODB_CONNECTION=mongodb+srv://user:password@cluster.mongodb.net/...

# Flask config
FLASK_ENV=development
PORT=5000
```

Start the backend server. You have two options depending on your environment:

**Option A (Recommended for Local Dev):** Start the highly-resilient SQLite Fallback server:
```bash
python app_fallback.py
```

**Option B (For Production):** Start the full MongoDB server:
```bash
python app_mongodb.py
```

### 3. Frontend Setup

Open a new terminal and navigate to the frontend directory:
```bash
cd frontend
```

Install the required Node dependencies:
```bash
npm install
```

Start the React development server:
```bash
npm start
```
The application will be accessible at `http://localhost:3000`.

---

## 🔍 System Status & Architecture

The application is built with resilience in mind. You can check the current health and availability of the AI models by visiting `http://localhost:5000/api/health`.

### Normal Operation (Groq API + MongoDB)
When the Groq API key is valid and MongoDB is connected, the system uses complex vector embeddings to deeply understand document context and generates highly contextual, conversational responses.

### Fallback Mode ⚠️
If either the MongoDB connection fails (e.g., due to Network/SSL restrictions) or the Groq API key is invalid/rate-limited, the system falls back to a robust local mode:
- SQLite is used for document storage.
- Keyword matching algorithms are used to retrieve information directly from documents without AI summaries.

## 📝 Troubleshooting 

| Symptom | Cause | Solution |
| --- | --- | --- |
| **"Invalid API Key" Error (401)** | The Groq API key is missing or incorrect. | Ensure `.env` contains `GROQ_API_KEY` with a valid key from the [Groq Console](https://console.groq.com/). Verify `app_fallback.py` is configured to use `os.getenv("GROQ_API_KEY")`. |
| **"Failed to fetch" (Login/Signup)** | SSL/TLS connection issue with MongoDB Atlas. | Your network/firewall may be blocking the connection. Stop `app_mongodb.py` and run the fallback server `app_fallback.py` instead. |
| **Infinite Restart Loop on Backend** | Watchdog detecting background file changes in Python `site-packages`. | Edit `app.run` inside your backend script and set `use_reloader=False`. |
| **File Upload (400 Error)** | Document format is empty, lacks readable text, or is a duplicate. | Ensure PDFs are text-based (not scanned images), and check backend console logs for specific "Upload Error" messages. |

## 👨‍💻 Development

### Key Directories
- `backend/app_fallback.py`: The robust fallback server logic (SQLite + Keyword matching)
- `backend/app_enhanced_mongodb.py`: The full-featured server logic (MongoDB + Vector Embeddings)
- `frontend/src/`: Contains mapping logic for all React components

---
*Developed for robust, local AI interactions.*
# Agentic_Rag
# Agentic_Rag_1
