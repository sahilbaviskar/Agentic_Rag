from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import tempfile
import PyPDF2
import io
import time
import sqlite3
import hashlib
import bcrypt
import jwt
from datetime import datetime, timedelta
from functools import wraps
import json
import re
from groq import Groq

app = Flask(__name__)
CORS(app)

# Configuration
GROQ_API_KEY = "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"
JWT_SECRET = "your-secret-key-change-in-production"

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# Initialize SQLite database
def init_db():
    """Initialize SQLite database for fallback"""
    conn = sqlite3.connect('agentic_rag.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Create documents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            metadata TEXT,
            doc_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('agentic_rag.db')
    conn.row_factory = sqlite3.Row
    return conn

def generate_token(user_id, email):
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return {"success": True, "user_id": payload['user_id'], "email": payload['email']}
    except jwt.ExpiredSignatureError:
        return {"success": False, "message": "Token expired"}
    except jwt.InvalidTokenError:
        return {"success": False, "message": "Invalid token"}

def require_auth(f):
    """Decorator to require authentication for endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        auth_result = verify_token(token)
        if not auth_result['success']:
            return jsonify({'error': auth_result['message']}), 401
        
        # Add user info to request context
        request.user_id = auth_result['user_id']
        request.user_email = auth_result['email']
        
        return f(*args, **kwargs)
    return decorated_function

def extract_text_from_pdf(file_content):
    """Extract text from PDF file content"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip() if text.strip() else None
    except Exception as e:
        print(f"Error reading PDF: {str(e)}")
        return None

def extract_text_from_file(file_content, filename):
    """Extract text based on file type"""
    file_extension = filename.lower().split('.')[-1]
    
    if file_extension == 'pdf':
        return extract_text_from_pdf(file_content)
    elif file_extension in ['txt', 'md', 'markdown']:
        try:
            return file_content.decode('utf-8').strip()
        except Exception as e:
            print(f"Error reading text file: {str(e)}")
            return None
    else:
        return None

# Authentication endpoints
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        
        if not email or not password or not name:
            return jsonify({'error': 'Email, password, and name are required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'User already exists'}), 400
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user
        cursor.execute(
            'INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)',
            (email, name, password_hash)
        )
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Generate token
        token = generate_token(user_id, email)
        
        return jsonify({
            'message': 'User created successfully',
            'token': token,
            'user': {'id': user_id, 'email': email, 'name': name}
        }), 201
        
    except Exception as e:
        print(f"Error in signup: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Find user
        cursor.execute('SELECT id, name, password_hash FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'error': 'User not found'}), 401
        
        # Check password
        if bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
            # Update last login
            cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))
            conn.commit()
            conn.close()
            
            # Generate token
            token = generate_token(user['id'], email)
            
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': {'id': user['id'], 'email': email, 'name': user['name']}
            }), 200
        else:
            conn.close()
            return jsonify({'error': 'Invalid password'}), 401
            
    except Exception as e:
        print(f"Error in login: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/verify', methods=['GET'])
@require_auth
def verify_token_endpoint():
    """Verify if the current token is valid"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM users WHERE id = ?', (request.user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify({
            'message': 'Token is valid',
            'user': {'id': request.user_id, 'email': request.user_email, 'name': user['name']}
        }), 200
    else:
        return jsonify({'error': 'User not found'}), 404

def search_documents(query, user_id, max_results=3):
    """Search through user documents using basic text matching"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all documents for the user
    cursor.execute('SELECT id, text, metadata FROM documents WHERE user_id = ?', (user_id,))
    documents = cursor.fetchall()
    conn.close()
    
    if not documents:
        return []
    
    # Simple keyword-based search
    query_words = re.findall(r'\w+', query.lower())
    scored_docs = []
    
    for doc in documents:
        text = doc['text'].lower()
        metadata = json.loads(doc['metadata'])
        
        # Calculate simple relevance score based on keyword matches
        score = 0
        matched_words = []
        
        for word in query_words:
            if word in text:
                # Count occurrences and boost score
                count = text.count(word)
                score += count
                matched_words.append(word)
        
        if score > 0:
            # Extract relevant snippet around matches
            snippet = extract_relevant_snippet(doc['text'], query_words)
            
            scored_docs.append({
                'id': str(doc['id']),
                'text': snippet,
                'metadata': metadata,
                'score': score,
                'matched_words': matched_words
            })
    
    # Sort by score and return top results
    scored_docs.sort(key=lambda x: x['score'], reverse=True)
    return scored_docs[:max_results]

def extract_relevant_snippet(text, query_words, snippet_length=500):
    """Extract a relevant snippet from the document"""
    text_lower = text.lower()
    
    # Find the first occurrence of any query word
    first_match_pos = len(text)
    for word in query_words:
        pos = text_lower.find(word)
        if pos != -1 and pos < first_match_pos:
            first_match_pos = pos
    
    if first_match_pos == len(text):
        # No matches found, return beginning of text
        return text[:snippet_length] + "..." if len(text) > snippet_length else text
    
    # Extract snippet around the match
    start = max(0, first_match_pos - snippet_length // 2)
    end = min(len(text), start + snippet_length)
    
    snippet = text[start:end]
    
    # Add ellipsis if needed
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    
    return snippet

def generate_response_with_groq(query, context, source_info):
    """Generate response using Groq API"""
    system_prompt = """You are a helpful AI assistant that answers questions based on provided context from the user's personal document collection.

IMPORTANT INSTRUCTIONS:
1. If the context contains relevant information from documents, use it to answer the question and clearly specify that the information comes from the user's documents.
2. If the context is empty or doesn't contain relevant information, generate a helpful response using your knowledge but CLEARLY STATE that this information is generated by the AI and not from the user's documents.
3. Always be transparent about your information sources.
4. Provide accurate and helpful responses.
5. Keep responses concise and focused.
6. Be conversational and friendly."""

    user_prompt = f"""Query: {query}

Context from user's documents: {context}

Source Information: {source_info}

Please answer the query based on the above context. Remember to clearly indicate whether your response is based on the user's documents or generated from your general knowledge."""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"Error generating response with Groq: {e}")
        return f"I found some relevant information in your documents, but I'm having trouble generating a detailed response right now. Here's what I found: {context[:200]}..."

# Enhanced RAG endpoints with basic search
@app.route('/api/query', methods=['POST'])
@require_auth
def process_query():
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query.strip():
            return jsonify({'error': 'Query cannot be empty'}), 400
        
        print(f"Processing query for user {request.user_id}: {query}")
        
        # Search through user documents
        relevant_docs = search_documents(query, request.user_id)
        
        if relevant_docs:
            # Prepare context from relevant documents
            context = "\n\n".join([doc["text"] for doc in relevant_docs])
            source_info = f"Information retrieved from {len(relevant_docs)} document(s): " + \
                         ", ".join([doc["metadata"].get("filename", f"doc_{doc['id']}") for doc in relevant_docs])
            
            # Generate response using Groq
            response = generate_response_with_groq(query, context, source_info)
            
            print(f"Query processed successfully. Retrieved {len(relevant_docs)} documents")
            
            return jsonify({
                'response': response,
                'retrieved_documents': relevant_docs,
                'source_info': source_info,
                'context_used': context,
                'tts_enabled': False
            })
        else:
            # No relevant documents found
            response = generate_response_with_groq(
                query, 
                "No relevant documents found in your personal database.", 
                "No documents available - response generated using LLM knowledge"
            )
            
            return jsonify({
                'response': response,
                'retrieved_documents': [],
                'source_info': 'No relevant documents found - response generated using AI knowledge',
                'context_used': None,
                'tts_enabled': False
            })
        
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
@require_auth
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        print(f"Received file upload from user {request.user_id}: {file.filename}")
        
        # Read file content
        file_content = file.read()
        filename = file.filename
        
        # Extract text from file
        text_content = extract_text_from_file(file_content, filename)
        
        if not text_content or len(text_content.strip()) < 10:
            return jsonify({'error': 'Could not extract meaningful text from file'}), 400
        
        # Create metadata
        metadata = {
            'filename': filename,
            'source': 'uploaded_document',
            'file_type': filename.split('.')[-1].lower(),
            'file_size': len(file_content),
            'upload_time': str(int(time.time()))
        }
        
        # Store document in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        doc_hash = hashlib.md5(text_content.encode()).hexdigest()
        
        # Check for duplicates
        cursor.execute('SELECT id FROM documents WHERE user_id = ? AND doc_hash = ?', (request.user_id, doc_hash))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Document already exists'}), 400
        
        # Insert document
        cursor.execute(
            'INSERT INTO documents (user_id, text, metadata, doc_hash) VALUES (?, ?, ?, ?)',
            (request.user_id, text_content, json.dumps(metadata), doc_hash)
        )
        conn.commit()
        conn.close()
        
        print(f"Document {filename} added successfully for user {request.user_id}")
        return jsonify({
            'message': 'File uploaded and processed successfully',
            'filename': filename,
            'text_length': len(text_content),
            'success': True
        })
        
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
@require_auth
def get_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user document stats
        cursor.execute('SELECT COUNT(*) as count FROM documents WHERE user_id = ?', (request.user_id,))
        doc_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT SUM(LENGTH(text)) as total_chars FROM documents WHERE user_id = ?', (request.user_id,))
        total_chars = cursor.fetchone()['total_chars'] or 0
        
        conn.close()
        
        stats = {
            'total_documents': doc_count,
            'total_characters': total_chars,
            'document_types': {},
            'tts_available': False
        }
        
        print(f"Returning stats for user {request.user_id}: {stats}")
        
        return jsonify(stats)
        
    except Exception as e:
        print(f"Error getting stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear', methods=['POST'])
@require_auth
def clear_database():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Clear documents for the authenticated user only
        cursor.execute('DELETE FROM documents WHERE user_id = ?', (request.user_id,))
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return jsonify({'message': f'Cleared {deleted_count} documents successfully'})
        
    except Exception as e:
        print(f"Error clearing documents: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'rag_available': False,  # Fallback mode
            'database': 'sqlite',
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time()
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("Starting Enhanced Fallback Flask backend server...")
    print("Features:")
    print("- User authentication (signup/login)")
    print("- SQLite local storage")
    print("- Document upload and text extraction")
    print("- Basic keyword-based document search")
    print("- Groq AI-powered responses")
    print("- Document-based question answering")
    
    app.run(debug=True, host='0.0.0.0', port=5000)