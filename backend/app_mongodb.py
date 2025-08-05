from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import tempfile
import PyPDF2
import io
import time
from functools import wraps

# Add the parent directory to sys.path to import your existing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentic_rag_mongodb import AgenticRAGMongoDB

app = Flask(__name__)
CORS(app)

# Configuration
GROQ_API_KEY = "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"
MONGODB_CONNECTION = "mongodb+srv://lokeshdeshmukh34:WB92y35PCAkCDZeB@cluster0.wqwbsbp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Initialize RAG system
rag_system = None

def get_rag_system():
    global rag_system
    if rag_system is None:
        try:
            rag_system = AgenticRAGMongoDB(GROQ_API_KEY, MONGODB_CONNECTION)
            print("MongoDB RAG system initialized successfully")
        except Exception as e:
            print(f"Error initializing RAG system: {e}")
            return None
    return rag_system

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
        
        rag = get_rag_system()
        if not rag:
            return jsonify({'error': 'RAG system not available'}), 500
        
        auth_result = rag.verify_token(token)
        if not auth_result['success']:
            return jsonify({'error': auth_result['message']}), 401
        
        # Add user info to request context
        request.user_id = auth_result['user_id']
        request.user = auth_result['user']
        
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
        
        rag = get_rag_system()
        if not rag:
            return jsonify({'error': 'RAG system not available'}), 500
        
        result = rag.signup(email, password, name)
        
        if result['success']:
            return jsonify({
                'message': result['message'],
                'token': result['token'],
                'user': result['user']
            }), 201
        else:
            return jsonify({'error': result['message']}), 400
            
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
        
        rag = get_rag_system()
        if not rag:
            return jsonify({'error': 'RAG system not available'}), 500
        
        result = rag.login(email, password)
        
        if result['success']:
            return jsonify({
                'message': result['message'],
                'token': result['token'],
                'user': result['user']
            }), 200
        else:
            return jsonify({'error': result['message']}), 401
            
    except Exception as e:
        print(f"Error in login: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/verify', methods=['GET'])
@require_auth
def verify_token():
    """Verify if the current token is valid"""
    return jsonify({
        'message': 'Token is valid',
        'user': request.user
    }), 200

# RAG endpoints (require authentication)
@app.route('/api/query', methods=['POST'])
@require_auth
def process_query():
    try:
        data = request.get_json()
        query = data.get('query', '')
        enable_tts = data.get('enable_tts', False)
        
        if not query.strip():
            return jsonify({'error': 'Query cannot be empty'}), 400
        
        rag = get_rag_system()
        if not rag:
            return jsonify({'error': 'RAG system not available'}), 500
        
        print(f"Processing query for user {request.user_id}: {query}")
        
        # Use the MongoDB RAG system
        result = rag.query(query, request.user_id, enable_tts=enable_tts)
        
        print(f"Query processed successfully. Retrieved {len(result.get('retrieved_documents', []))} documents")
        
        return jsonify(result)
        
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
        
        rag = get_rag_system()
        if not rag:
            return jsonify({'error': 'RAG system not available'}), 500
        
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
        
        # Add document to RAG system for the authenticated user
        success = rag.add_document(text_content, metadata, request.user_id)
        
        if success:
            print(f"Document {filename} added successfully for user {request.user_id}")
            return jsonify({
                'message': 'File uploaded and processed successfully',
                'filename': filename,
                'text_length': len(text_content),
                'success': True
            })
        else:
            return jsonify({'error': 'Failed to add document - possibly duplicate'}), 400
        
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
@require_auth
def get_stats():
    try:
        rag = get_rag_system()
        if not rag:
            return jsonify({'error': 'RAG system not available'}), 500
        
        # Get user-specific statistics
        stats = rag.get_user_stats(request.user_id)
        
        print(f"Returning stats for user {request.user_id}: {stats}")
        
        return jsonify(stats)
        
    except Exception as e:
        print(f"Error getting stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear', methods=['POST'])
@require_auth
def clear_database():
    try:
        rag = get_rag_system()
        if not rag:
            return jsonify({'error': 'RAG system not available'}), 500
        
        # Clear documents for the authenticated user only
        result = rag.clear_user_documents(request.user_id)
        
        if result:
            return jsonify({'message': 'Your documents cleared successfully'})
        else:
            return jsonify({'error': 'Failed to clear documents'}), 500
        
    except Exception as e:
        print(f"Error clearing documents: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        rag = get_rag_system()
        return jsonify({
            'status': 'healthy',
            'rag_available': rag is not None,
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
    print("Starting MongoDB-based Flask backend server...")
    print("Features:")
    print("- User authentication (signup/login)")
    print("- MongoDB vector storage")
    print("- Improved text-to-speech")
    print("- User-specific document management")
    
    app.run(debug=True, host='0.0.0.0', port=5000)