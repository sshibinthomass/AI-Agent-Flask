from src.langgraphagenticai.graph.basic_chatbot_graph import BasicChatbotGraph
from src.langgraphagenticai.graph.restaurant_recommendation_graph import (
    RestaurantRecommendationGraph,
)
from src.langgraphagenticai.graph.agentic_chatbot_graph import AgenticChatbotGraph
from src.langgraphagenticai.graph.test_mcp_graph import TestMCPGraph
from dotenv import load_dotenv

load_dotenv()


class GraphBuilder:
    def __init__(self, model, user_controls_input, message):
        self.llm = model
        self.user_controls_input = user_controls_input
        self.message = message
        self.current_llm = user_controls_input["selected_llm"]

    def setup_graph(self, usecase: str):
        """
        Sets up the graph for the selected use case.
        """
        if usecase == "Sushi":
            restaurant_graph = RestaurantRecommendationGraph(self.llm)
            return restaurant_graph.chatbot_restaurant_recommendation()
        elif usecase == "Agentic Chatbot":
            agentic_chatbot_graph = AgenticChatbotGraph(self.llm)
            return agentic_chatbot_graph.graph
        elif usecase == "Test MCP":
            test_mcp_graph = TestMCPGraph(self.llm)
            return test_mcp_graph.test_mcp_graph()
        else:
            basic_chatbot_graph = BasicChatbotGraph(self.llm)
            return basic_chatbot_graph.basic_chatbot_build_graph()
