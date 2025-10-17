import streamlit as st
import asyncio
from src.langgraphagenticai.ui.streamlitui.loadui import LoadStreamlitUI
from src.langgraphagenticai.LLMS.groqllm import GroqLLM
from src.langgraphagenticai.LLMS.ollamallm import OllamaLLM
from src.langgraphagenticai.LLMS.geminillm import GeminiLLM
from src.langgraphagenticai.LLMS.openAIllm import OpenAILLM
from src.langgraphagenticai.graph.graph_builder import GraphBuilder
from langchain_core.messages import HumanMessage, AIMessage
from src.langgraphagenticai.tools.return_prompt import return_prompt

def extract_content(val):
    if isinstance(val, (HumanMessage, AIMessage)):
        return val.content
    return val

def load_langgraph_agenticai_app():
    """
    Loads and runs the LangGraph AgenticAI application with Streamlit UI.
    This function initializes the UI, handles user input, configures the LLM model,
    sets up the graph based on the selected use case, and displays the output while 
    implementing exception handling for robustness.

    """

    ##Load UI
    ui=LoadStreamlitUI()
    user_input=ui.load_streamlit_ui()

    if not user_input: #This is the user input from the UI if no user input is found then error is shown
        st.error("Error: Failed to load user input from the UI.")
        return
    
    user_message = st.chat_input("Enter your message:") #This is the user message from the UI

    # Initialize chat history in session state if not present
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []

    # Initialize session ID for consistent chat history across LLMs
    if 'session_id' not in st.session_state:
        st.session_state['session_id'] = "streamlit_session"

    # Initialize or get existing LLM config object to maintain chat history
    current_llm = user_input["selected_llm"]
    #print(user_message)
    # Check if we need to create a new LLM config (first time or LLM changed)
    if ('llm_config' not in st.session_state or
        'current_llm_type' not in st.session_state or
        st.session_state['current_llm_type'] != current_llm):

        try:
            ## Configure The LLM's with chat history support
            if current_llm == "Groq":
                st.session_state['llm_config'] = GroqLLM(user_contols_input=user_input)
                base_llm = st.session_state['llm_config'].get_base_llm()

            elif current_llm == "OpenAI":
                st.session_state['llm_config'] = OpenAILLM(user_controls_input=user_input)
                base_llm = st.session_state['llm_config'].get_base_llm()

            elif current_llm == "Gemini":
                st.session_state['llm_config'] = GeminiLLM(user_controls_input=user_input)
                base_llm = st.session_state['llm_config'].get_base_llm()

            elif current_llm == "Ollama":
                st.session_state['llm_config'] = OllamaLLM(user_controls_input=user_input)
                base_llm = st.session_state['llm_config'].get_base_llm()

            # Store the current LLM type
            st.session_state['current_llm_type'] = current_llm



        except Exception as e:
            st.error(f"Error: LLM configuration failed- {e}")
            return
    else:
        base_llm = st.session_state['llm_config'].get_base_llm()

    if user_message:
        try:
            #History
            # Initialize and set up the graph based on use case
            usecase = user_input.get("selected_usecase")
            if not usecase:
                st.error("Error: No use case selected.")
                return
            # Prepare the initial state with full chat history (for context)
            system_prompt = return_prompt(usecase)
            #Adding system prompt to the messages
            messages = [{"role": "system", "content": system_prompt}]
            #Adding previous responses from llm to the messages

            # Add only the last 20 messages (or all if less than 20)
            last_n_messages = st.session_state['chat_history'][-int(ui.config.get_chat_history_length()):] if len(st.session_state['chat_history']) > int(ui.config.get_chat_history_length()) else st.session_state['chat_history']
            messages += [{"role": msg["role"], "content": extract_content(msg["content"])} for msg in last_n_messages]

            #adding current user message to the messages
            if(len(messages) > int(ui.config.get_chat_history_length())):
                messages.pop(1)
            messages.append({"role": "user", "content": user_message})


            #initial state is the messages
            initial_state = {"messages": messages}

            #Building the graph
            graph_builder = GraphBuilder(model=base_llm,user_controls_input=user_input,message=user_message)
            graph = graph_builder.setup_graph(usecase)

            # Run the graph (async, since RestaurantRecommendationNode is async)
            result = asyncio.run(graph.ainvoke(initial_state, config={"configurable": {"session_id": st.session_state['session_id']}}))
            # Get the assistant's reply robustly
            assistant_reply = ""
            if isinstance(result["messages"], list):
                last_message = result["messages"][-1] if result["messages"] else ""
                if isinstance(last_message, dict):
                    assistant_reply = last_message.get("content", "")
                else:
                    assistant_reply = last_message
            elif isinstance(result["messages"], dict):
                assistant_reply = result["messages"].get("content", "")
            else:
                assistant_reply = result["messages"]
            # Append user and assistant messages to chat history
            st.session_state['chat_history'].append({"role": "user", "content": user_message})
            st.session_state['chat_history'].append({"role": "assistant", "content": assistant_reply})

        except Exception as e:
            st.error(f"Error: Chat processing or graph execution failed - {e}")
            return

    # Display the full chat history

    for msg in st.session_state['chat_history']:
        with st.chat_message(msg["role"]):
            content = msg["content"]
            if isinstance(content, dict) and "content" in content:
                st.write(content["content"])
            elif isinstance(content, (HumanMessage, AIMessage)):
                st.write(content.content)
            elif isinstance(content, str):
                st.write(content)
            else:
                st.write(str(content))

    # Add a button to clear chat history
    if st.sidebar.button("Clear Chat History"):
        st.session_state['chat_history'] = []
        if 'llm_config' in st.session_state:
            st.session_state['llm_config'].clear_chat_history(st.session_state['session_id'])
        st.rerun()
