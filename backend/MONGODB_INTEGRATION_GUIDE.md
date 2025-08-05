# MongoDB Integration Guide for Agentic RAG System

## Overview

This guide explains the enhanced MongoDB integration for the Agentic RAG system, which now stores all user signup data and vector data for the RAG system in MongoDB.

## Features

### 🔐 User Authentication with MongoDB
- **User Registration**: All signup data (email, name, hashed password) stored in MongoDB
- **Secure Login**: Password verification using bcrypt hashing
- **JWT Tokens**: Secure authentication tokens with 7-day expiration
- **User Statistics**: Track document count and character count per user

### 📊 Vector Storage in MongoDB
- **Document Embeddings**: All document vectors stored in MongoDB
- **Metadata Storage**: File information, upload time, file type, etc.
- **Chunking Support**: Large documents split into chunks for better retrieval
- **Duplicate Detection**: Prevents duplicate document uploads

### 🔍 Advanced Search Capabilities
- **Vector Search**: Cosine similarity-based document retrieval
- **Hybrid Search**: Combines vector similarity with keyword matching
- **Relevance Scoring**: Advanced scoring algorithm for better results
- **Context Extraction**: Smart snippet extraction for large documents

## Database Schema

### Users Collection
```javascript
{
  "_id": ObjectId,
  "email": "user@example.com",
  "name": "User Name",
  "password_hash": "bcrypt_hash",
  "created_at": ISODate,
  "last_login": ISODate,
  "document_count": 0,
  "total_characters": 0
}
```

### Documents Collection
```javascript
{
  "_id": ObjectId,
  "user_id": "user_object_id",
  "text": "document_content",
  "embedding": [0.1, 0.2, ...], // 384-dimensional vector
  "metadata": {
    "filename": "document.pdf",
    "file_type": "pdf",
    "file_size": 12345,
    "upload_time": "2024-01-01T00:00:00",
    "chunk_index": 0,
    "total_chunks": 3,
    "chunk_size": 1000
  },
  "doc_hash": "md5_hash",
  "created_at": ISODate,
  "text_length": 1000
}
```

## Database Indexes

The system automatically creates optimized indexes for better performance:

### Users Collection Indexes
- `email` (unique) - Fast user lookup by email
- `created_at` - User registration analytics

### Documents Collection Indexes
- `user_id` - Fast document retrieval per user
- `doc_hash` - Duplicate detection
- `user_id + doc_hash` (unique) - Prevent user-specific duplicates
- `metadata.filename` - File-based searches
- `metadata.file_type` - Filter by file type
- `created_at` - Document upload analytics

## API Endpoints

### Authentication Endpoints

#### POST /api/auth/signup
Register a new user
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "User Name"
}
```

#### POST /api/auth/login
Login existing user
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

#### GET /api/auth/verify
Verify JWT token (requires Authorization header)

### Document Management Endpoints

#### POST /api/upload
Upload and process documents (requires authentication)
- Supports PDF, TXT, MD files
- Automatic text extraction
- Vector embedding generation
- Chunking for large documents

#### POST /api/query
Query the RAG system (requires authentication)
```json
{
  "query": "What is machine learning?"
}
```

#### GET /api/stats
Get user document statistics (requires authentication)

#### POST /api/clear
Clear all user documents (requires authentication)

### System Endpoints

#### GET /api/health
System health check

## Configuration

### Environment Variables

Create a `.env.mongodb` file with the following variables:

```bash
# Required
GROQ_API_KEY=your_groq_api_key
MONGODB_CONNECTION=your_mongodb_connection_string

# Optional
JWT_SECRET=your_jwt_secret
FLASK_ENV=development
PORT=5000
DATABASE_NAME=agentic_rag
```

### MongoDB Connection String Format
```
mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority&appName=YourApp
```

## Installation and Setup

### 1. Install Dependencies
```bash
pip install -r requirements_enhanced.txt
```

### 2. Configure Environment
Copy `.env.mongodb` and update with your credentials:
```bash
cp .env.mongodb.example .env.mongodb
# Edit .env.mongodb with your actual credentials
```

### 3. Start the Server
```bash
python start_mongodb_server.py
```

Or directly:
```bash
python app_enhanced_mongodb.py
```

## Security Features

### Password Security
- **bcrypt Hashing**: Industry-standard password hashing
- **Salt Generation**: Unique salt for each password
- **No Plain Text**: Passwords never stored in plain text

### JWT Security
- **Secure Tokens**: HS256 algorithm for token signing
- **Expiration**: 7-day token expiration
- **User Validation**: Token validation on each request

### Data Isolation
- **User-Specific Data**: Each user can only access their own documents
- **Secure Queries**: All database queries filtered by user ID
- **Authorization Required**: All document operations require valid JWT

## Performance Optimizations

### Database Optimizations
- **Compound Indexes**: Optimized for common query patterns
- **Connection Pooling**: Efficient MongoDB connection management
- **Aggregation Pipelines**: Efficient statistics calculation

### Search Optimizations
- **Vector Caching**: Embeddings cached in database
- **Hybrid Scoring**: Balanced vector and keyword search
- **Result Limiting**: Configurable result limits for performance

### Memory Management
- **Streaming**: Large file processing with streaming
- **Chunking**: Documents split for better memory usage
- **Garbage Collection**: Proper cleanup of temporary objects

## Monitoring and Logging

### Health Monitoring
- **Service Status**: Real-time service health checks
- **Database Connectivity**: MongoDB connection monitoring
- **Component Status**: Individual component health tracking

### Logging
- **Structured Logging**: JSON-formatted logs for analysis
- **Error Tracking**: Comprehensive error logging
- **Performance Metrics**: Query timing and performance logs

## Troubleshooting

### Common Issues

#### MongoDB Connection Issues
```bash
# Check connection string format
# Ensure IP whitelist includes your IP
# Verify username/password credentials
```

#### Authentication Issues
```bash
# Check JWT_SECRET configuration
# Verify token expiration
# Ensure proper Authorization header format
```

#### Search Performance Issues
```bash
# Check database indexes
# Monitor query execution time
# Consider document chunking optimization
```

### Debug Mode
Enable debug mode for detailed logging:
```bash
export FLASK_ENV=development
python app_enhanced_mongodb.py
```

## Production Deployment

### Environment Configuration
```bash
export FLASK_ENV=production
export JWT_SECRET=your_secure_production_secret
export MONGODB_CONNECTION=your_production_mongodb_url
```

### Security Checklist
- [ ] Change default JWT secret
- [ ] Use production MongoDB cluster
- [ ] Enable MongoDB authentication
- [ ] Configure proper CORS settings
- [ ] Set up SSL/TLS certificates
- [ ] Configure rate limiting
- [ ] Set up monitoring and alerting

### Scaling Considerations
- **Database Sharding**: For large user bases
- **Read Replicas**: For improved read performance
- **Caching Layer**: Redis for frequently accessed data
- **Load Balancing**: Multiple application instances

## API Usage Examples

### Complete User Flow
```python
import requests

# 1. Register user
signup_response = requests.post('http://localhost:5000/api/auth/signup', json={
    'email': 'user@example.com',
    'password': 'password123',
    'name': 'Test User'
})
token = signup_response.json()['token']

# 2. Upload document
headers = {'Authorization': f'Bearer {token}'}
with open('document.pdf', 'rb') as f:
    upload_response = requests.post(
        'http://localhost:5000/api/upload',
        files={'file': f},
        headers=headers
    )

# 3. Query documents
query_response = requests.post(
    'http://localhost:5000/api/query',
    json={'query': 'What is this document about?'},
    headers=headers
)

print(query_response.json()['response'])
```

## Support and Maintenance

### Regular Maintenance Tasks
- **Index Optimization**: Monitor and optimize database indexes
- **Data Cleanup**: Remove orphaned documents and expired tokens
- **Performance Monitoring**: Track query performance and optimize
- **Security Updates**: Keep dependencies updated

### Backup Strategy
- **Database Backups**: Regular MongoDB backups
- **Configuration Backups**: Environment and configuration files
- **Recovery Testing**: Regular backup restoration testing

## Conclusion

The enhanced MongoDB integration provides a robust, scalable, and secure foundation for the Agentic RAG system. With comprehensive user management, efficient vector storage, and advanced search capabilities, the system is ready for production deployment while maintaining excellent performance and security standards.