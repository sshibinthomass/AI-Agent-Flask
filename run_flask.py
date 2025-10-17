#!/usr/bin/env python3
"""
Flask Application Startup Script
Run this script to start the Flask chat application
"""

import os
import sys
from flask_app import app, socketio

if __name__ == "__main__":
    print("Starting Flask Chat Application...")
    print("Features:")
    print("- Multiple LLM Support (Groq, OpenAI, Gemini, Ollama)")
    print("- Real-time WebSocket Communication")
    print("- Modern UI with Bootstrap")
    print("- Chat History Management")
    print("- MCP Server Integration")
    print("- LangGraph AI Agent Integration")
    print("\nAccess the application at: http://localhost:5000")
    print("Press Ctrl+C to stop the server")

    try:
        # Use threading mode for Python 3.13 compatibility
        socketio.run(app, debug=True, host="0.0.0.0", port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\nShutting down Flask application...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting Flask application: {e}")
        sys.exit(1)
