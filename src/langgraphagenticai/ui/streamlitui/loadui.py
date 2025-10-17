import streamlit as st
import os
from dotenv import load_dotenv
import subprocess
import sys
load_dotenv()

#Import the config file
#from file location and name import class
from src.langgraphagenticai.ui.uiconfigfile import Config

def start_mcp_servers():
    # Get absolute paths to the MCP tool scripts
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../tools'))
    parking_script = os.path.join(base_dir, 'mcp_parking.py')
    restaurant_script = os.path.join(base_dir, 'mcp_restaurant.py')

    # Start both as background processes (creationflags for Windows, close_fds for Unix)
    subprocess.Popen([sys.executable, parking_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.Popen([sys.executable, restaurant_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Start MCP servers when Streamlit app starts
start_mcp_servers()

class LoadStreamlitUI:
    def __init__(self):
        self.config=Config() #Config class is imported from the config file(uiconfigfile.py)
        self.user_controls={} #This is a dictionary to store the user controls

    def load_streamlit_ui(self):
        page_title=self.config.get_page_title()
        st.set_page_config(page_title= page_title, layout="wide") #This is the title of the streamlit app
        st.header(page_title) #This is the header of the streamlit app from the config file

        with st.sidebar: #This is the sidebar of the streamlit app
            # Get options from config
            llm_options = self.config.get_llm_options() #This is a list of LLM options from the config file
            usecase_options = self.config.get_usecase_options() #This is a list of Usecase options from the config file

            # LLM selection
            self.user_controls["selected_llm"] = st.selectbox("Select LLM", llm_options)

            if self.user_controls["selected_llm"] == 'Groq': #This is the Groq model selection
                # Model selection
                model_options = self.config.get_groq_model_options() #This is a list of Groq model options from the config file
                self.user_controls["selected_groq_model"] = st.selectbox("Select Model", model_options) #This is the Groq model selection
                self.user_controls["GROQ_API_KEY"] =os.getenv("GROQ_API_KEY")

            if self.user_controls["selected_llm"] == 'OpenAI': #This is the OpenAI model selection
                # Model selection
                model_options = self.config.get_openai_model_options() #This is a list of OpenAI model options from the config file
                self.user_controls["selected_openai_model"] = st.selectbox("Select Model", model_options) #This is the OpenAI model selection
                self.user_controls["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

            if self.user_controls["selected_llm"] == 'Gemini': #This is the Gemini model selection
                # Model selection
                model_options = self.config.get_gemini_model_options() #This is a list of Gemini model options from the config file
                self.user_controls["selected_gemini_model"] = st.selectbox("Select Model", model_options) #This is the Gemini model selection
                self.user_controls["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")

            if self.user_controls["selected_llm"] == 'Ollama': #This is the Ollama model selection
                # Model selection
                model_options = self.config.get_ollama_model_options() #This is a list of Ollama model options from the config file
                self.user_controls["selected_ollama_model"] = st.selectbox("Select Model", model_options) #This is the Ollama model selection
                self.user_controls["OLLAMA_API_KEY"] = os.getenv("OLLAMA_API_KEY")

            ## USecase selection
            self.user_controls["selected_usecase"]=st.selectbox("Select Usecases",usecase_options) #This is the Usecase selection from the config file

        return self.user_controls