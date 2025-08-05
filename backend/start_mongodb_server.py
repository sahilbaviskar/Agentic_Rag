#!/usr/bin/env python3
"""
Startup script for Enhanced MongoDB RAG Server
This script loads environment variables and starts the Flask application
"""

import os
import sys
from pathlib import Path

def load_env_file(env_file_path):
    """Load environment variables from .env file"""
    if os.path.exists(env_file_path):
        print(f"Loading environment variables from {env_file_path}")
        with open(env_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        return True
    return False

def main():
    """Main startup function"""
    print("=" * 60)
    print("Enhanced MongoDB RAG Server Startup")
    print("=" * 60)
    
    # Get the directory of this script
    script_dir = Path(__file__).parent
    
    # Try to load environment variables
    env_files = [
        script_dir / '.env.mongodb',
        script_dir / '.env',
        script_dir / '.env.production'
    ]
    
    env_loaded = False
    for env_file in env_files:
        if load_env_file(env_file):
            env_loaded = True
            break
    
    if not env_loaded:
        print("Warning: No environment file found. Using default values.")
        print("Available environment files to create:")
        for env_file in env_files:
            print(f"  - {env_file}")
    
    # Check required environment variables
    required_vars = ['GROQ_API_KEY', 'MONGODB_CONNECTION']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your environment or .env file")
        sys.exit(1)
    
    # Display configuration
    print("\nConfiguration:")
    print(f"  MongoDB Connection: {'✓ Configured' if os.getenv('MONGODB_CONNECTION') else '✗ Missing'}")
    print(f"  Groq API Key: {'✓ Configured' if os.getenv('GROQ_API_KEY') else '✗ Missing'}")
    print(f"  JWT Secret: {'✓ Configured' if os.getenv('JWT_SECRET') else '✗ Using default'}")
    print(f"  Port: {os.getenv('PORT', '5000')}")
    print(f"  Environment: {os.getenv('FLASK_ENV', 'development')}")
    
    print("\nFeatures enabled:")
    print("  ✓ User Authentication with MongoDB")
    print("  ✓ Vector Document Storage in MongoDB")
    print("  ✓ Hybrid Search (Vector + Keyword)")
    print("  ✓ Document Chunking")
    print("  ✓ Comprehensive Statistics")
    print("  ✓ Optimized Database Indexes")
    print("  ✓ Production-ready Deployment")
    
    print("\n" + "=" * 60)
    print("Starting Flask Application...")
    print("=" * 60)
    
    # Import and run the Flask app
    try:
        from app_enhanced_mongodb import app
        
        port = int(os.getenv('PORT', 5000))
        debug_mode = os.getenv('FLASK_ENV', 'development') == 'development'
        
        print(f"\nServer will be available at: http://localhost:{port}")
        print("Press Ctrl+C to stop the server")
        print("-" * 60)
        
        app.run(debug=debug_mode, host='0.0.0.0', port=port)
        
    except ImportError as e:
        print(f"Error importing Flask app: {e}")
        print("Make sure app_enhanced_mongodb.py is in the same directory")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()