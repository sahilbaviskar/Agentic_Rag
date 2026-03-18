# 🚀 Agentic RAG System - Improved Setup Guide

## 🔧 Quick Fix for Current Issues

### Issue 1: Invalid Groq API Key
**Problem**: The logs show "Invalid API Key" error from Groq.

**Solution**:
1. Get a new Groq API key from [https://console.groq.com/](https://console.groq.com/)
2. Run the setup script:
   ```bash
   cd c:\nlp_ai\Final_hacknova\Agentic_Rag\backend
   python setup_groq_api.py
   ```
3. Or manually update the `.env` file:
   ```
   GROQ_API_KEY=your_new_valid_groq_api_key_here
   ```

### Issue 2: System Now Has Fallback Responses
**Improvement**: The system now continues working even if Groq API is unavailable.

**Features Added**:
- ✅ Graceful fallback when Groq API fails
- ✅ Direct document content extraction
- ✅ Clear indication when AI processing is unavailable
- ✅ System continues functioning for document upload and search

## 🎯 Current System Capabilities

### ✅ Working Features (Even Without Groq)
1. **Document Upload & Processing**
   - PDF text extraction
   - Document chunking
   - Vector embeddings generation
   - MongoDB storage

2. **Document Search & Retrieval**
   - Vector similarity search
   - Keyword matching
   - Hybrid search combining both approaches

3. **User Management**
   - User registration and authentication
   - JWT token-based sessions
   - User-specific document isolation

4. **Fallback Response System**
   - Direct document content extraction
   - Basic keyword-based responses
   - Clear status indicators

### 🔄 Enhanced Features (With Valid Groq API)
1. **AI-Powered Responses**
   - Context-aware answer generation
   - Natural language processing
   - Intelligent summarization

2. **Advanced Query Processing**
   - Complex question answering
   - Multi-document synthesis
   - Conversational responses

## 🛠️ Setup Instructions

### Step 1: Install Dependencies
```bash
cd c:\nlp_ai\Final_hacknova\Agentic_Rag\backend
pip install -r requirements_enhanced.txt
```

### Step 2: Configure API Key
```bash
python setup_groq_api.py
```

### Step 3: Start the Server
```bash
python app_enhanced_mongodb.py
```

### Step 4: Test the System
1. Open your browser to `http://localhost:5000/api/health`
2. Check the service status
3. Use the frontend to test document upload and queries

## 🔍 Troubleshooting Guide

### Problem: "Invalid API Key" Error
**Symptoms**: 
- Error code 401 from Groq API
- System falls back to basic responses

**Solutions**:
1. **Get New API Key**:
   - Visit [Groq Console](https://console.groq.com/)
   - Create account or login
   - Generate new API key
   - Copy key (starts with `gsk_`)

2. **Update Configuration**:
   ```bash
   python setup_groq_api.py
   ```

3. **Manual Update**:
   Edit `.env` file:
   ```
   GROQ_API_KEY=gsk_your_actual_api_key_here
   ```

### Problem: MongoDB Connection Issues
**Symptoms**:
- "Failed to connect to MongoDB" errors
- System won't start

**Solutions**:
1. **Check Connection String**:
   Verify MongoDB URL in `.env`:
   ```
   MONGODB_CONNECTION=mongodb+srv://username:password@cluster.mongodb.net/...
   ```

2. **Test Connection**:
   ```bash
   python -c "from pymongo import MongoClient; import certifi; client = MongoClient('your_connection_string', tlsCAFile=certifi.where()); print('Connected:', client.admin.command('ping'))"
   ```

### Problem: Embedding Model Loading Issues
**Symptoms**:
- "Failed to load embedding model" errors
- Document upload fails

**Solutions**:
1. **Install Dependencies**:
   ```bash
   pip install sentence-transformers torch
   ```

2. **Clear Cache and Retry**:
   ```bash
   python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
   ```

## 📊 System Status Indicators

### Health Check Endpoint
Visit: `http://localhost:5000/api/health`

**Response Example**:
```json
{
  "status": "healthy",
  "services": {
    "groq": true,
    "embedding_model": true,
    "mongodb": true,
    "mongodb_connection": true,
    "storage_type": "mongodb"
  },
  "timestamp": 1234567890
}
```

### Service Status Meanings
- ✅ `"groq": true` - AI responses available
- ⚠️ `"groq": false` - Fallback responses only
- ✅ `"embedding_model": true` - Document processing works
- ✅ `"mongodb": true` - Database storage works

## 🔄 Fallback Response Examples

### When Groq API is Unavailable
**Query**: "What is data science?"
**Response**: 
```
Here's what I found in your documents related to 'What is data science?': 
[Document content excerpt...]

[Note: This response is extracted directly from your documents. AI processing is currently unavailable.]
```

### When No Documents Found
**Query**: "Tell me about machine learning"
**Response**:
```
I found your query about 'Tell me about machine learning' but couldn't locate relevant information in your uploaded documents. The AI service is currently unavailable to provide a general response. Please try uploading relevant documents or try again later when the AI service is restored.
```

## 🚀 Next Steps

1. **Fix Groq API Key**: Run `python setup_groq_api.py`
2. **Test Document Upload**: Upload a PDF through the frontend
3. **Test Queries**: Ask questions about your uploaded documents
4. **Monitor Logs**: Check console output for any issues

## 📞 Support

If you continue experiencing issues:

1. **Check Logs**: Look for specific error messages in the console
2. **Verify Services**: Use the health check endpoint
3. **Test Components**: Run the setup script to verify each service
4. **Restart System**: Sometimes a fresh restart resolves connection issues

The system is now much more robust and will continue working even when some services are unavailable, providing a better user experience overall.