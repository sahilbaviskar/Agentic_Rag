from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import tempfile
import PyPDF2
import io
import time
import ssl
from functools import wraps
import json
import re
import hashlib
import bcrypt
import jwt
from datetime import datetime, timedelta
from groq import Groq
from sentence_transformers import SentenceTransformer
import numpy as np
import logging
import pymongo
from pymongo import MongoClient
from bson import ObjectId
import certifi



# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration - Use environment variables for production
GROQ_API_KEY = os.getenv('GROQ_API_KEY', "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")
JWT_SECRET = os.getenv('JWT_SECRET', "your-production-secret-key-change-this")
#MONGODB_CONNECTION = os.getenv('MONGODB_CONNECTION', "mongodb+srv://lokeshdeshmukh34:WB92y35PCAkCDZeB@cluster0.wqwbsbp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
#mongodb+srv://baviskarsahil2005:OHSyigOLMu0OjtNK@cluster0.u2ckqrs.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
MONGODB_CONNECTION = os.getenv('MONGODB_CONNECTION', "mongodb+srv://baviskarsahil2005:OHSyigOLMu0OjtNK@cluster0.u2ckqrs.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# Initialize global components
groq_client = None
embedding_model = None
mongo_client = None
db = None

class MongoDBManager:
    """Enhanced MongoDB manager for user and document operations"""
    
    def __init__(self, connection_string: str, database_name: str = "agentic_rag"):
        try:
            # Configure MongoDB client with SSL settings
              

            self.client = MongoClient(
                connection_string,
                tls=True,
                tlsCAFile=certifi.where(),  # Correct and secure
                connectTimeoutMS=30000,
                socketTimeoutMS=30000,
                serverSelectionTimeoutMS=30000,
                maxPoolSize=10
            )

            
            # Test the connection
            self.client.admin.command('ping')
            
            self.db = self.client[database_name]
            self.users_collection = self.db.users
            self.documents_collection = self.db.documents
            
            # Create indexes for better performance
            self._create_indexes()
            
            logger.info("MongoDB Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB: {e}")
            raise
    
    def _create_indexes(self):
        """Create necessary indexes for optimal performance"""
        try:
            # User indexes
            self.users_collection.create_index([("email", 1)], unique=True)
            self.users_collection.create_index([("created_at", 1)])
            
            # Document indexes
            self.documents_collection.create_index([("user_id", 1)])
            self.documents_collection.create_index([("doc_hash", 1)])
            self.documents_collection.create_index([("user_id", 1), ("doc_hash", 1)], unique=True)
            self.documents_collection.create_index([("metadata.filename", 1)])
            self.documents_collection.create_index([("metadata.file_type", 1)])
            self.documents_collection.create_index([("created_at", 1)])
            
            logger.info("MongoDB indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    # User Management Methods
    def create_user(self, email: str, name: str, password_hash: bytes) -> str:
        """Create a new user and return user ID"""
        user_doc = {
            "email": email,
            "name": name,
            "password_hash": password_hash,
            "created_at": datetime.utcnow(),
            "last_login": None,
            "document_count": 0,
            "total_characters": 0
        }
        
        result = self.users_collection.insert_one(user_doc)
        return str(result.inserted_id)
    
    def find_user_by_email(self, email: str) -> dict:
        """Find user by email"""
        return self.users_collection.find_one({"email": email})
    
    def find_user_by_id(self, user_id: str) -> dict:
        """Find user by ID"""
        try:
            return self.users_collection.find_one({"_id": ObjectId(user_id)})
        except:
            return None
    
    def update_user_login(self, user_id: str):
        """Update user's last login time"""
        try:
            self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"last_login": datetime.utcnow()}}
            )
        except Exception as e:
            logger.error(f"Error updating user login: {e}")
    
    def update_user_stats(self, user_id: str, doc_count_delta: int = 0, char_count_delta: int = 0):
        """Update user document statistics"""
        try:
            update_doc = {}
            if doc_count_delta != 0:
                update_doc["$inc"] = {"document_count": doc_count_delta}
            if char_count_delta != 0:
                if "$inc" not in update_doc:
                    update_doc["$inc"] = {}
                update_doc["$inc"]["total_characters"] = char_count_delta
            
            if update_doc:
                self.users_collection.update_one(
                    {"_id": ObjectId(user_id)},
                    update_doc
                )
        except Exception as e:
            logger.error(f"Error updating user stats: {e}")
    
    # Document Management Methods
    def add_document(self, user_id: str, text: str, embedding: list, metadata: dict, doc_hash: str) -> str:
        """Add a document with its embedding"""
        doc = {
            "user_id": user_id,
            "text": text,
            "embedding": embedding,
            "metadata": metadata,
            "doc_hash": doc_hash,
            "created_at": datetime.utcnow(),
            "text_length": len(text)
        }
        
        try:
            result = self.documents_collection.insert_one(doc)
            # Update user stats
            self.update_user_stats(user_id, doc_count_delta=1, char_count_delta=len(text))
            return str(result.inserted_id)
        except pymongo.errors.DuplicateKeyError:
            logger.warning(f"Duplicate document detected for user {user_id}")
            return None
    
    def find_documents_by_user(self, user_id: str) -> list:
        """Get all documents for a user"""
        return list(self.documents_collection.find({"user_id": user_id}))
    
    def document_exists(self, user_id: str, doc_hash: str) -> bool:
        """Check if a document already exists for the user"""
        return self.documents_collection.find_one({"user_id": user_id, "doc_hash": doc_hash}) is not None
    
    def delete_user_documents(self, user_id: str) -> int:
        """Delete all documents for a user"""
        try:
            # Get current stats before deletion
            user_docs = list(self.documents_collection.find({"user_id": user_id}, {"text_length": 1}))
            total_chars = sum(doc.get("text_length", 0) for doc in user_docs)
            doc_count = len(user_docs)
            
            # Delete documents
            result = self.documents_collection.delete_many({"user_id": user_id})
            
            # Update user stats
            if result.deleted_count > 0:
                self.update_user_stats(user_id, doc_count_delta=-doc_count, char_count_delta=-total_chars)
            
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error deleting user documents: {e}")
            return 0
    
    def get_user_document_stats(self, user_id: str) -> tuple:
        """Get comprehensive document statistics for a user"""
        try:
            # Aggregate statistics
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": None,
                    "total_docs": {"$sum": 1},
                    "total_chars": {"$sum": "$text_length"},
                    "avg_doc_length": {"$avg": "$text_length"}
                }}
            ]
            
            result = list(self.documents_collection.aggregate(pipeline))
            if result:
                stats = result[0]
                total_docs = stats["total_docs"]
                total_chars = stats["total_chars"]
                avg_length = int(stats["avg_doc_length"]) if stats["avg_doc_length"] else 0
            else:
                total_docs = total_chars = avg_length = 0
            
            # Get document types
            type_pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {"_id": "$metadata.file_type", "count": {"$sum": 1}}}
            ]
            
            doc_types = {}
            for item in self.documents_collection.aggregate(type_pipeline):
                doc_types[item["_id"] or "unknown"] = item["count"]
            
            return total_docs, total_chars, doc_types, avg_length
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return 0, 0, {}, 0
    
    def search_documents_vector(self, user_id: str, query_embedding: list, max_results: int = 5) -> list:
        """Search documents using vector similarity"""
        try:
            user_docs = self.find_documents_by_user(user_id)
            
            if not user_docs:
                return []
            
            # Calculate cosine similarity
            query_embedding = np.array(query_embedding)
            similarities = []
            
            for doc in user_docs:
                doc_embedding = np.array(doc["embedding"])
                # Cosine similarity
                similarity = np.dot(query_embedding, doc_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
                )
                similarities.append((similarity, doc))
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[0], reverse=True)
            
            results = []
            for similarity, doc in similarities[:max_results]:
                if similarity > 0.1:  # Minimum similarity threshold
                    results.append({
                        "id": str(doc["_id"]),
                        "text": doc["text"],
                        "metadata": doc["metadata"],
                        "similarity": float(similarity),
                        "distance": 1 - float(similarity)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []

def init_components():
    """Initialize all components with proper error handling"""
    global groq_client, embedding_model, mongo_client, db
    
    try:
        # Initialize Groq client
        groq_client = Groq(api_key=GROQ_API_KEY)
        logger.info("Groq client initialized successfully")
        
        # Initialize embedding model
        logger.info("Loading embedding model...")
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Embedding model loaded successfully")
        
        # Initialize MongoDB
        logger.info("Connecting to MongoDB...")
        db = MongoDBManager(MONGODB_CONNECTION)
        logger.info("MongoDB connected successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        return False

# Initialize components on startup
if not init_components():
    logger.error("Failed to initialize required components")
    sys.exit(1)

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
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        auth_result = verify_token(token)
        if not auth_result['success']:
            return jsonify({'error': auth_result['message']}), 401
        
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
        logger.error(f"Error reading PDF: {str(e)}")
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
            logger.error(f"Error reading text file: {str(e)}")
            return None
    else:
        return None

def chunk_text(text, chunk_size=1000, overlap=200):
    """Split text into overlapping chunks for better retrieval"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            for i in range(end, max(start + chunk_size - 200, start), -1):
                if text[i] in '.!?':
                    end = i + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks

def search_documents_hybrid(query, user_id, max_results=5):
    """Hybrid search combining vector and keyword search"""
    try:
        if not embedding_model or not db:
            return []
        
        # Generate query embedding
        query_embedding = embedding_model.encode(query).tolist()
        
        # Get vector search results
        vector_results = db.search_documents_vector(user_id, query_embedding, max_results * 2)
        
        if not vector_results:
            return []
        
        # Add keyword scoring
        query_words = re.findall(r'\w+', query.lower())
        
        for doc in vector_results:
            text_lower = doc['text'].lower()
            keyword_score = 0
            matched_words = []
            
            for word in query_words:
                if word in text_lower:
                    count = text_lower.count(word)
                    keyword_score += count
                    matched_words.append(word)
            
            # Normalize keyword score
            normalized_keyword = min(keyword_score / 10.0, 1.0)
            
            # Combined score (70% vector, 30% keyword)
            combined_score = (0.7 * doc['similarity']) + (0.3 * normalized_keyword)
            
            doc['keyword_score'] = keyword_score
            doc['combined_score'] = float(combined_score)
            doc['matched_words'] = matched_words
        
        # Sort by combined score and return top results
        vector_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return vector_results[:max_results]
        
    except Exception as e:
        logger.error(f"Error in hybrid search: {e}")
        return []

def generate_response_with_groq(query, context, source_info):
    """Generate response using Groq API"""
    system_prompt = """You are a helpful AI assistant that answers questions based on provided context from the user's personal document collection.

IMPORTANT INSTRUCTIONS:
1. If the context contains relevant information from documents, use it to answer the question and clearly specify that the information comes from the user's documents.
2. If the context is empty or doesn't contain relevant information, generate a helpful response using your knowledge but CLEARLY STATE that this information is generated by the AI and not from the user's documents.
3. Always be transparent about your information sources.
4. Provide accurate and helpful responses.
5. Keep responses concise and focused.
6. Be conversational and friendly.
7. If you find specific information in the documents, quote it directly."""

    user_prompt = f"""Query: {query}

Context from user's documents: {context}

Source Information: {source_info}

Please answer the query based on the above context. Remember to clearly indicate whether your response is based on the user's documents or generated from your general knowledge."""

    try:
        if not groq_client:
            return "AI service is currently unavailable. Please try again later."
        
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
        logger.error(f"Error generating response with Groq: {e}")
        if context and context.strip():
            return f"Based on your documents: {context[:300]}..."
        return "I'm having trouble generating a response right now. Please try again later."

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
        
        # Check if user already exists
        if db.find_user_by_email(email):
            return jsonify({'error': 'User already exists'}), 400
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user
        user_id = db.create_user(email, name, password_hash)
        
        # Generate token
        token = generate_token(user_id, email)
        
        logger.info(f"New user created: {email} (ID: {user_id})")
        
        return jsonify({
            'message': 'User created successfully',
            'token': token,
            'user': {'id': user_id, 'email': email, 'name': name}
        }), 201
        
    except Exception as e:
        logger.error(f"Error in signup: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user
        user = db.find_user_by_email(email)
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        # Check password
        if bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
            user_id = str(user['_id'])
            
            # Update last login
            db.update_user_login(user_id)
            
            token = generate_token(user_id, email)
            
            logger.info(f"User logged in: {email} (ID: {user_id})")
            
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': {'id': user_id, 'email': email, 'name': user['name']}
            }), 200
        else:
            return jsonify({'error': 'Invalid password'}), 401
            
    except Exception as e:
        logger.error(f"Error in login: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/verify', methods=['GET'])
@require_auth
def verify_token_endpoint():
    """Verify if the current token is valid"""
    try:
        user = db.find_user_by_id(request.user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'message': 'Token is valid',
            'user': {'id': request.user_id, 'email': request.user_email, 'name': user['name']}
        }), 200
        
    except Exception as e:
        logger.error(f"Error in token verification: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/query', methods=['POST'])
@require_auth
def process_query():
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query.strip():
            return jsonify({'error': 'Query cannot be empty'}), 400
        
        logger.info(f"Processing query for user {request.user_id}: {query}")
        
        # Search through user documents using hybrid approach
        relevant_docs = search_documents_hybrid(query, request.user_id)
        
        if relevant_docs:
            # Prepare context from relevant documents
            context_parts = []
            for doc in relevant_docs:
                text = doc['text']
                if len(text) > 500:
                    # Extract relevant snippet
                    query_words = re.findall(r'\w+', query.lower())
                    text_lower = text.lower()
                    
                    best_pos = 0
                    best_score = 0
                    
                    for i in range(0, len(text) - 500, 100):
                        snippet = text_lower[i:i+500]
                        score = sum(snippet.count(word) for word in query_words)
                        if score > best_score:
                            best_score = score
                            best_pos = i
                    
                    if best_score > 0:
                        text = "..." + text[best_pos:best_pos+500] + "..."
                    else:
                        text = text[:500] + "..."
                
                context_parts.append(text)
            
            context = "\n\n".join(context_parts)
            source_info = f"Information retrieved from {len(relevant_docs)} document(s): " + \
                         ", ".join([doc["metadata"].get("filename", f"doc_{doc['id'][:8]}") for doc in relevant_docs])
            
            # Generate response using Groq
            response = generate_response_with_groq(query, context, source_info)
            
            logger.info(f"Query processed successfully. Retrieved {len(relevant_docs)} documents")
            
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
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
@require_auth
def upload_file():
    try:
        if not embedding_model:
            return jsonify({'error': 'Embedding service not available'}), 500
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        logger.info(f"Received file upload from user {request.user_id}: {file.filename}")
        
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
            'upload_time': datetime.utcnow().isoformat()
        }
        
        # Check for duplicates
        doc_hash = hashlib.md5(text_content.encode()).hexdigest()
        
        if db.document_exists(request.user_id, doc_hash):
            return jsonify({'error': 'Document already exists'}), 400
        
        # Split text into chunks for better retrieval
        chunks = chunk_text(text_content)
        
        # Process each chunk
        documents_added = 0
        for i, chunk in enumerate(chunks):
            try:
                # Generate embedding for the chunk
                embedding = embedding_model.encode(chunk).tolist()
                
                # Create chunk metadata
                chunk_metadata = metadata.copy()
                chunk_metadata['chunk_index'] = i
                chunk_metadata['total_chunks'] = len(chunks)
                chunk_metadata['chunk_size'] = len(chunk)
                
                chunk_hash = hashlib.md5(chunk.encode()).hexdigest()
                
                # Store document
                doc_id = db.add_document(request.user_id, chunk, embedding, chunk_metadata, chunk_hash)
                
                if doc_id:
                    documents_added += 1
                
            except Exception as e:
                logger.error(f"Error processing chunk {i}: {e}")
                continue
        
        if documents_added > 0:
            logger.info(f"Document {filename} processed into {documents_added} chunks for user {request.user_id}")
            return jsonify({
                'message': f'File uploaded and processed successfully into {documents_added} chunks',
                'filename': filename,
                'text_length': len(text_content),
                'chunks_created': documents_added,
                'success': True
            })
        else:
            return jsonify({'error': 'Failed to process document'}), 500
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
@require_auth
def get_stats():
    try:
        # Get comprehensive user statistics
        total_docs, total_chars, doc_types, avg_length = db.get_user_document_stats(request.user_id)
        
        # Get user info
        user = db.find_user_by_id(request.user_id)
        user_created = user.get('created_at', datetime.utcnow()) if user else datetime.utcnow()
        
        stats = {
            'total_documents': total_docs,
            'total_characters': total_chars,
            'average_document_length': avg_length,
            'document_types': doc_types,
            'user_created': user_created.isoformat(),
            'storage_type': 'mongodb',
            'tts_available': False
        }
        
        logger.info(f"Returning stats for user {request.user_id}: {stats}")
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear', methods=['POST'])
@require_auth
def clear_database():
    try:
        deleted_count = db.delete_user_documents(request.user_id)
        
        logger.info(f"Cleared {deleted_count} documents for user {request.user_id}")
        
        return jsonify({'message': f'Cleared {deleted_count} documents successfully'})
        
    except Exception as e:
        logger.error(f"Error clearing documents: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        services = {
            'groq': groq_client is not None,
            'embedding_model': embedding_model is not None,
            'mongodb': db is not None,
            'storage_type': 'mongodb'
        }
        
        # Test MongoDB connection
        if db:
            try:
                db.client.admin.command('ping')
                services['mongodb_connection'] = True
            except:
                services['mongodb_connection'] = False
        
        all_healthy = all(services.values())
        
        return jsonify({
            'status': 'healthy' if all_healthy else 'degraded',
            'services': services,
            'timestamp': time.time()
        }), 200 if all_healthy else 503
        
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
    print("Starting Enhanced MongoDB RAG Server...")
    print("Features:")
    print("- User authentication (signup/login) with MongoDB storage")
    print("- Vector-based document search with MongoDB storage")
    print("- Hybrid search (vector + keyword)")
    print("- Document chunking for better retrieval")
    print("- Comprehensive user statistics")
    print("- Optimized MongoDB indexes")
    print("- Groq AI-powered responses")
    print("- Production-ready deployment")
    print("- Speech-to-Text support via frontend")
    
    # Check services
    print(f"✅ MongoDB: {'Connected' if db else 'Unavailable'}")
    print(f"✅ Groq: {'Available' if groq_client else 'Unavailable'}")
    print(f"✅ Embedding Model: {'Available' if embedding_model else 'Unavailable'}")
    
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_ENV', 'development') == 'development'
    
    # Fix for Windows socket error - use threaded mode and disable reloader in production
    try:
        if debug_mode:
            print("⚠️  Running in debug mode - file changes will trigger restart")
            print("⚠️  If you encounter socket errors, restart the server manually")
            app.run(debug=True, host='0.0.0.0', port=port, threaded=True, use_reloader=True)
        else:
            print("🚀 Running in production mode")
            app.run(debug=False, host='0.0.0.0', port=port, threaded=True)
    except OSError as e:
        if "10038" in str(e):
            print("⚠️  Socket error detected. Restarting without reloader...")
            app.run(debug=False, host='0.0.0.0', port=port, threaded=True, use_reloader=False)
        else:
            raise e