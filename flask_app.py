from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import asyncio
import threading
import subprocess
import sys
from dotenv import load_dotenv
import uuid
import json
from datetime import datetime

# Import existing modules
from src.langgraphagenticai.ui.uiconfigfile import Config
from src.langgraphagenticai.LLMS.groqllm import GroqLLM
from src.langgraphagenticai.LLMS.ollamallm import OllamaLLM
from src.langgraphagenticai.LLMS.geminillm import GeminiLLM
from src.langgraphagenticai.LLMS.openAIllm import OpenAILLM
from src.langgraphagenticai.graph.graph_builder import GraphBuilder
from src.langgraphagenticai.tools.return_prompt import return_prompt
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "your-secret-key-here")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Global storage for chat sessions
chat_sessions = {}
llm_configs = {}


def extract_content(val):
    """Extract content from various message types"""
    if isinstance(val, (HumanMessage, AIMessage)):
        # Extract just the content from LangChain message objects
        return str(val.content) if val.content else ""
    elif isinstance(val, dict):
        # Handle dictionary messages
        content = val.get("content", "")
        if isinstance(content, (HumanMessage, AIMessage)):
            return str(content.content) if content.content else ""
        return str(content)
    else:
        return str(val)


def start_mcp_servers():
    """Start MCP servers in background"""
    try:
        base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "src/langgraphagenticai/tools")
        )
        parking_script = os.path.join(base_dir, "mcp_parking.py")
        restaurant_script = os.path.join(base_dir, "mcp_restaurant.py")

        # Start both as background processes
        subprocess.Popen(
            [sys.executable, parking_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.Popen(
            [sys.executable, restaurant_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("MCP servers started successfully")
    except Exception as e:
        print(f"Error starting MCP servers: {e}")


# Start MCP servers when Flask app starts
start_mcp_servers()


@app.route("/")
def index():
    """Main page with chat interface"""
    config = Config()
    return render_template(
        "index.html",
        page_title=config.get_page_title(),
        llm_options=config.get_llm_options(),
        usecase_options=config.get_usecase_options(),
        groq_models=config.get_groq_model_options(),
        openai_models=config.get_openai_model_options(),
        gemini_models=config.get_gemini_model_options(),
        ollama_models=config.get_ollama_model_options(),
    )


@app.route("/api/config")
def get_config():
    """API endpoint to get configuration options"""
    config = Config()
    return jsonify(
        {
            "llm_options": config.get_llm_options(),
            "usecase_options": config.get_usecase_options(),
            "groq_models": config.get_groq_model_options(),
            "openai_models": config.get_openai_model_options(),
            "gemini_models": config.get_gemini_model_options(),
            "ollama_models": config.get_ollama_model_options(),
            "chat_history_length": config.get_chat_history_length(),
        }
    )


@socketio.on("connect")
def handle_connect():
    """Handle client connection"""
    session_id = str(uuid.uuid4())
    session["session_id"] = session_id
    join_room(session_id)
    chat_sessions[session_id] = []
    print(f"New session created: {session_id}")
    emit("connected", {"session_id": session_id})


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection"""
    session_id = session.get("session_id")
    if session_id:
        leave_room(session_id)
        if session_id in chat_sessions:
            del chat_sessions[session_id]
        if session_id in llm_configs:
            del llm_configs[session_id]


@socketio.on("send_message")
def handle_message(data):
    """Handle incoming chat messages"""
    session_id = session.get("session_id")
    print(f"Handling message for session: {session_id}")

    if not session_id:
        emit("error", {"message": "No session found"})
        return

    user_message = data.get("message", "")
    selected_llm = data.get("selected_llm", "")
    selected_model = data.get("selected_model", "")
    selected_usecase = data.get("selected_usecase", "")

    print(f"Message: {user_message}")
    print(f"LLM: {selected_llm}, Model: {selected_model}, Usecase: {selected_usecase}")

    if not all([user_message, selected_llm, selected_usecase]):
        emit("error", {"message": "Missing required parameters"})
        return

    try:
        # Prepare user controls
        user_controls = {
            "selected_llm": selected_llm,
            "selected_usecase": selected_usecase,
        }

        # Add model selection based on LLM
        if selected_llm == "Groq":
            user_controls["selected_groq_model"] = selected_model
            user_controls["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
        elif selected_llm == "OpenAI":
            user_controls["selected_openai_model"] = selected_model
            user_controls["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
        elif selected_llm == "Gemini":
            user_controls["selected_gemini_model"] = selected_model
            user_controls["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")
        elif selected_llm == "Ollama":
            user_controls["selected_ollama_model"] = selected_model
            user_controls["OLLAMA_API_KEY"] = os.getenv("OLLAMA_API_KEY")

        # Initialize or get existing LLM config
        if (
            session_id not in llm_configs
            or llm_configs[session_id]["llm_type"] != selected_llm
        ):
            if selected_llm == "Groq":
                llm_config = GroqLLM(user_contols_input=user_controls)
            elif selected_llm == "OpenAI":
                llm_config = OpenAILLM(user_controls_input=user_controls)
            elif selected_llm == "Gemini":
                llm_config = GeminiLLM(user_controls_input=user_controls)
            elif selected_llm == "Ollama":
                llm_config = OllamaLLM(user_controls_input=user_controls)

            llm_configs[session_id] = {"config": llm_config, "llm_type": selected_llm}

        base_llm = llm_configs[session_id]["config"].get_base_llm()

        # Get chat history
        chat_history = chat_sessions.get(session_id, [])

        # Prepare messages with system prompt
        system_prompt = return_prompt(selected_usecase)
        messages = [{"role": "system", "content": system_prompt}]

        # Add chat history (last 20 messages)
        config = Config()
        chat_history_length = int(config.get_chat_history_length())
        last_n_messages = (
            chat_history[-chat_history_length:]
            if len(chat_history) > chat_history_length
            else chat_history
        )
        messages += [
            {"role": msg["role"], "content": extract_content(msg["content"])}
            for msg in last_n_messages
        ]

        # Add current user message
        if len(messages) > chat_history_length:
            messages.pop(1)
        messages.append({"role": "user", "content": user_message})

        # Prepare initial state
        initial_state = {"messages": messages}

        # Build and run the graph
        graph_builder = GraphBuilder(
            model=base_llm, user_controls_input=user_controls, message=str(user_message)
        )
        graph = graph_builder.setup_graph(selected_usecase)

        # Run the graph asynchronously
        def run_graph():
            try:
                print(f"Running graph for session: {session_id}")
                print(f"Initial state: {initial_state}")
                result = asyncio.run(
                    graph.ainvoke(
                        initial_state,
                        config={"configurable": {"session_id": str(session_id)}},
                    )
                )
                print(f"Graph result: {result}")

                # Extract assistant reply properly
                assistant_reply = ""
                if isinstance(result["messages"], list):
                    last_message = result["messages"][-1] if result["messages"] else ""
                    assistant_reply = extract_content(last_message)
                elif isinstance(result["messages"], dict):
                    assistant_reply = extract_content(result["messages"])
                else:
                    assistant_reply = extract_content(result["messages"])

                # Update chat history (ensure content is string, not AIMessage object)
                chat_sessions[session_id].append(
                    {"role": "user", "content": str(user_message)}
                )
                chat_sessions[session_id].append(
                    {"role": "assistant", "content": str(assistant_reply)}
                )

                # Emit response (ensure all values are JSON serializable)
                socketio.emit(
                    "message_response",
                    {
                        "user_message": str(user_message),
                        "assistant_reply": str(assistant_reply),
                        "timestamp": datetime.now().isoformat(),
                    },
                    room=session_id,
                )

            except Exception as e:
                print(f"Error in run_graph: {str(e)}")
                print(f"Session ID: {session_id}")
                print(f"User message: {user_message}")
                socketio.emit(
                    "error",
                    {"message": f"Error processing message: {str(e)}"},
                    room=session_id,
                )

        # Run in thread to avoid blocking
        thread = threading.Thread(target=run_graph)
        thread.start()

    except Exception as e:
        emit("error", {"message": f"Error: {str(e)}"})


@socketio.on("clear_history")
def handle_clear_history():
    """Clear chat history for the session"""
    session_id = session.get("session_id")
    if session_id:
        chat_sessions[session_id] = []
        if session_id in llm_configs:
            llm_configs[session_id]["config"].clear_chat_history(session_id)
        emit("history_cleared")


@socketio.on("get_history")
def handle_get_history():
    """Get chat history for the session"""
    session_id = session.get("session_id")
    if session_id and session_id in chat_sessions:
        emit("chat_history", {"history": chat_sessions[session_id]})
    else:
        emit("chat_history", {"history": []})


if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
