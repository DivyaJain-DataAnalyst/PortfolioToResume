#!/usr/bin/env python3
"""
Simple script to start the Flask server for Portfolio to Resume Converter
"""

import os
import sys
import subprocess
import time
import requests

def check_flask_running():
    """Check if Flask server is already running"""
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Flask server is already running!")
            return True
    except:
        pass
    return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_content = """# API Keys for Portfolio to Resume Converter
# Replace these with your actual API keys

GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True

# Server Configuration
HOST=0.0.0.0
PORT=5000
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_content)
        print("📝 Created .env file with placeholder API keys")
        print("⚠️  Please update the API keys in .env file for full functionality")
    else:
        print("✅ .env file already exists")

def start_flask_server():
    """Start the Flask server"""
    print("🚀 Starting Flask server...")
    
    try:
        # Start Flask server in background
        process = subprocess.Popen([
            sys.executable, "app.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if server is running
        if check_flask_running():
            print("✅ Flask server started successfully!")
            print("🌐 Server URL: http://localhost:5000")
            print("📊 Health check: http://localhost:5000/health")
            print("🧪 Test endpoint: http://localhost:5000/test")
            return process
        else:
            print("❌ Failed to start Flask server")
            process.terminate()
            return None
            
    except Exception as e:
        print(f"❌ Error starting Flask server: {e}")
        return None

def main():
    print("🎯 Portfolio to Resume Converter - Flask Server Starter")
    print("=" * 50)
    
    # Check if already running
    if check_flask_running():
        return
    
    # Create .env file if needed
    create_env_file()
    
    # Start Flask server
    process = start_flask_server()
    
    if process:
        print("\n📋 Instructions:")
        print("1. The Flask server is now running on http://localhost:5000")
        print("2. Your Next.js frontend should now be able to connect")
        print("3. To stop the server, press Ctrl+C")
        print("4. For full functionality, update API keys in .env file")
        
        try:
            # Keep the script running
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping Flask server...")
            process.terminate()
            print("✅ Flask server stopped")
    else:
        print("\n❌ Failed to start Flask server")
        print("Please check the error messages above")

if __name__ == "__main__":
    main() 