# This class is used to load the config file and get the options for the UI
from configparser import ConfigParser
import requests
import os
import streamlit as st


class Config:
    def __init__(self,config_file="./src/langgraphagenticai/ui/uiconfigfile.ini"):
        self.config=ConfigParser()
        self.config.read(config_file)
        self.config_file=config_file
    
    #Use split to split the options into a list
    def get_llm_options(self):
        return self.config["DEFAULT"].get("LLM_OPTIONS").split(", ")
    
    def get_usecase_options(self):
        return self.config["DEFAULT"].get("USECASE_OPTIONS").split(", ")

    def get_groq_model_options(self):
        return self.config["DEFAULT"].get("GROQ_MODEL_OPTIONS").split(", ")

    def get_openai_model_options(self):
        return self.config["DEFAULT"].get("OPENAI_MODEL_OPTIONS").split(", ")
    
    def get_chat_history_length(self):
        return self.config["DEFAULT"].get("CHAT_HISTORY_LENGTH")
    
    def get_page_title(self):
        return self.config["DEFAULT"].get("PAGE_TITLE")

    def get_gemini_model_options(self):
        return self.config["DEFAULT"].get("GEMINI_MODEL_OPTIONS").split(", ")
    
    def get_ollama_model_options(self):
        return self.config["DEFAULT"].get("OLLAMA_MODEL_OPTIONS").split(", ")
    