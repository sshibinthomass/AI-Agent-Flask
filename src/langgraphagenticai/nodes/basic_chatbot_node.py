from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import sys
from dotenv import load_dotenv
from pathlib import Path
from src.langgraphagenticai.state.state import State
from datetime import datetime
import time

current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent
sys.path.append(str(project_root))

load_dotenv()


class BasicChatbotNode:
    """
    Basic Chatbot login implementation
    """

    def __init__(self, model):
        self.llm = model

    def process(self, state: State) -> dict:
        """
        Processes the input state and generates a chatbot response.
        """
        # Record start time
        start_time = datetime.now()
        start_timestamp = time.time()

        response = self.llm.invoke(state["messages"])

        # Record end time and calculate duration
        end_time = datetime.now()
        end_timestamp = time.time()
        response_time_seconds = end_timestamp - start_timestamp

        # Error handling for the response
        # If response is an AIMessage, return it as is
        if hasattr(response, "content"):
            return {
                "messages": response,
                "start_time": start_time,
                "end_time": end_time,
                "response_time_seconds": response_time_seconds,
            }
        # If response is a dict with 'content', create AIMessage
        if isinstance(response, dict) and "content" in response:
            return {
                "messages": AIMessage(content=response["content"]),
                "start_time": start_time,
                "end_time": end_time,
                "response_time_seconds": response_time_seconds,
            }
        # If response is a string, create AIMessage
        return {
            "messages": AIMessage(content=str(response)),
            "start_time": start_time,
            "end_time": end_time,
            "response_time_seconds": response_time_seconds,
        }


if __name__ == "__main__":
    # Create LLM instance
    llm = ChatGroq(model="qwen-qwq-32b")

    # Create BasicChatbotNode instance with the LLM
    node = BasicChatbotNode(llm)

    # Example conversation history
    conversation_history = [
        SystemMessage(content="You are a helpful and efficient assistant."),
        HumanMessage(content="Hi, how are you?"),
        AIMessage(content="Hello! How can I assist you today?"),
        HumanMessage(content="What is your name?"),
        AIMessage(content="My name is Chatbot. How can I assist you today?"),
        HumanMessage(content="What is the capital of France?"),
        AIMessage(content="The capital of France is Paris."),
    ]

    # Call the process method and print the result
    result = node.process(conversation_history)
    print("Result:", result)
