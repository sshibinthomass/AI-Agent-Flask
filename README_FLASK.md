# Flask Chat Application

A modern, real-time chat application built with Flask that replicates all features from the original Streamlit app.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_flask.txt
```

### 2. Start MCP Servers

```bash
python start_mcp_servers.py
```

### 3. Start Flask App

```bash
python run_flask.py
```

### 4. Access Application

Open your browser and navigate to `http://localhost:5000`

## Features

- **Multiple LLM Support**: Groq, OpenAI, Gemini, Ollama
- **Real-time WebSocket Communication**
- **Modern UI with Bootstrap**
- **Chat History Management**
- **MCP Server Integration**
- **LangGraph AI Agent Integration**
- **Table Formatting**: Proper HTML table rendering
- **Python 3.13 Compatible**

## Files

- `flask_app.py` - Main Flask application
- `run_flask.py` - Startup script
- `start_mcp_servers.py` - MCP server manager
- `requirements_flask.txt` - Flask dependencies
- `templates/index.html` - Chat interface template
- `static/css/style.css` - Styling
- `static/js/app.js` - Client-side JavaScript

## Environment Variables

Set up your API keys in `.env`:

```
SECRET_KEY=your-secret-key-here
GROQ_API_KEY=your-groq-api-key
OPENAI_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key
OLLAMA_API_KEY=your-ollama-api-key
```
