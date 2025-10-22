"""
MCP Server Selector Node Implementation

This module implements the MCP (Model Context Protocol) server selector node that:
1. Analyzes user queries using LLM to determine which MCP servers are needed
2. Maps query keywords to appropriate server types (restaurant, parking, weather)
3. Supports multi-server selection for complex queries
4. Provides fallback logic for server selection
5. Returns structured analysis and server recommendations

The selector uses both LLM-based analysis and keyword matching to ensure
robust server selection across different query types and user phrasings.
"""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import sys
from pathlib import Path
from src.langgraphagenticai.state.state import State
from datetime import datetime
import time

# Setup path resolution for imports
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent
sys.path.append(str(project_root))


class MCPServerSelectorNode:
    """
    Node to dynamically select appropriate MCP server based on user question

    This class analyzes user queries to determine which MCP servers would be
    most relevant for answering their questions. It uses a combination of:
    - LLM-based semantic analysis for intelligent server selection
    - Keyword matching as a fallback mechanism
    - Multi-server selection for complex queries
    - Comprehensive server mappings with descriptions and URLs
    """

    def __init__(self, model):
        """
        Initialize the MCP server selector with language model and server mappings

        Args:
            model: The language model instance for query analysis
        """
        self.llm = model
        # Comprehensive server mappings with keywords, URLs, and descriptions
        self.server_mappings = {
            "restaurant": {
                "keywords": [
                    "restaurant",
                    "sushi",
                    "food",
                    "menu",
                    "dining",
                    "eat",
                    "lunch",
                    "dinner",
                    "cuisine",
                    "meal",
                ],
                "server_name": "restaurant",
                "url": "http://127.0.0.1:8002/mcp",
                "description": "Restaurant information, reviews, and menu data",
            },
            "parking": {
                "keywords": [
                    "parking",
                    "park",
                    "spot",
                    "garage",
                    "lot",
                    "vehicle",
                    "car",
                    "space",
                ],
                "server_name": "Parking",
                "url": "http://127.0.0.1:8003/mcp",
                "description": "Parking availability and information",
            },
            "weather": {
                "keywords": [
                    "weather",
                    "temperature",
                    "rain",
                    "sunny",
                    "cloudy",
                    "climate",
                    "forecast",
                    "temperature",
                ],
                "server_name": "Weather",
                "url": "http://127.0.0.1:8004/mcp",
                "description": "Weather information and forecasts",
            },
        }

    def process(self, state: State) -> dict:
        """
        Analyzes the user question and selects appropriate MCP server(s)

        This is the main processing method that:
        1. Extracts the user's message from the conversation state
        2. Uses LLM analysis to determine which servers are relevant
        3. Falls back to keyword matching if LLM analysis fails
        4. Returns structured results with timing information

        Args:
            state: Workflow state containing user messages

        Returns:
            dict: Updated state with selected_servers, analysis, and timing
        """
        # Record start time for performance tracking
        start_time = datetime.now()
        start_timestamp = time.time()

        try:
            # Extract the latest user message from the conversation
            # This handles different message formats (objects, dicts, strings)
            user_message = ""
            for message in reversed(state["messages"]):
                if hasattr(message, "content"):
                    user_message = message.content
                    break
                elif isinstance(message, dict) and "content" in message:
                    user_message = message["content"]
                    break

            # Use LLM to analyze the question and determine which servers are needed
            # This provides intelligent semantic analysis beyond simple keyword matching
            analysis_prompt = f"""
            Analyze the following user question and determine which MCP servers would be most relevant.
            
            Available servers:
            1. restaurant: For restaurant information, reviews, menus, food-related queries
            2. parking: For parking availability, locations, payment methods  
            3. weather: For weather information, temperature, forecasts
            
            User question: "{user_message}"
            
            IMPORTANT: 
            - If the question mentions restaurants AND parking, select BOTH "restaurant" and "parking"
            - If the question mentions restaurants AND weather, select BOTH "restaurant" and "weather"  
            - If the question mentions parking AND weather, select BOTH "parking" and "weather"
            - If the question mentions all three, select "restaurant", "parking", and "weather"
            - Only select servers that are directly relevant to the question
            
            Return your analysis in this exact format:
            RELEVANT_SERVERS: [comma-separated list of server names]
            REASONING: [brief explanation of why these servers are relevant]
            """

            # Create structured messages for LLM analysis
            analysis_messages = [
                SystemMessage(
                    content="You are an expert at analyzing user questions and determining which data sources would be most relevant."
                ),
                HumanMessage(content=analysis_prompt),
            ]

            # Get LLM analysis of the query
            analysis_response = self.llm.invoke(analysis_messages)
            analysis_text = (
                analysis_response.content
                if hasattr(analysis_response, "content")
                else str(analysis_response)
            )

            # Parse the LLM response to extract relevant servers
            # This includes both structured parsing and keyword fallback
            relevant_servers = self._parse_server_selection(analysis_text, user_message)

            # Record end time and calculate total processing duration
            end_time = datetime.now()
            end_timestamp = time.time()
            response_time_seconds = end_timestamp - start_timestamp

            print("🔍 MCP Selector Debug:")
            print(f"   Selected servers: {relevant_servers}")
            print(f"   Analysis: {analysis_text[:100]}...")

            return {
                "messages": AIMessage(
                    content=f"Selected servers: {', '.join(relevant_servers)}"
                ),
                "selected_servers": relevant_servers,
                "analysis": analysis_text,
                "start_time": start_time,
                "end_time": end_time,
                "response_time_seconds": response_time_seconds,
            }

        except Exception as e:
            # Handle any errors in server selection gracefully
            # Record end time even for errors to maintain timing consistency
            end_time = datetime.now()
            end_timestamp = time.time()
            response_time_seconds = end_timestamp - start_timestamp

            return {
                "messages": AIMessage(content=f"Error in server selection: {str(e)}"),
                "selected_servers": [
                    "restaurant"
                ],  # Default fallback to restaurant server
                "analysis": f"Error: {str(e)}",
                "start_time": start_time,
                "end_time": end_time,
                "response_time_seconds": response_time_seconds,
            }

    def _parse_server_selection(self, analysis_text: str, user_message: str) -> list:
        """
        Parse the LLM analysis to determine which servers are relevant

        This method implements a two-tier parsing strategy:
        1. Structured parsing: Attempts to parse the LLM's structured response
        2. Keyword fallback: Uses keyword matching if structured parsing fails

        Args:
            analysis_text: The LLM's analysis response
            user_message: The original user message for keyword fallback

        Returns:
            list: List of selected server names
        """
        # First try to parse the structured response from the LLM
        # This is the preferred method as it uses semantic understanding
        if "RELEVANT_SERVERS:" in analysis_text:
            try:
                lines = analysis_text.split("\n")
                for line in lines:
                    if line.strip().startswith("RELEVANT_SERVERS:"):
                        servers_text = line.split("RELEVANT_SERVERS:")[1].strip()
                        # Parse comma-separated list of servers
                        servers = []
                        # Split by comma and clean up whitespace
                        server_list = [
                            s.strip().lower() for s in servers_text.split(",")
                        ]
                        # Validate against known server types
                        for server in ["restaurant", "parking", "weather"]:
                            if server in server_list:
                                servers.append(server)
                        if servers:
                            return servers
            except Exception:
                # If structured parsing fails, fall through to keyword matching
                pass

        # Fallback to keyword-based selection with improved logic
        # This ensures we always get a result even if LLM analysis fails
        user_lower = user_message.lower()
        selected_servers = []

        # Check for each server type using keyword matching
        for server_name, config in self.server_mappings.items():
            for keyword in config["keywords"]:
                if keyword in user_lower:
                    selected_servers.append(server_name)
                    break  # Only need one keyword match per server type

        # Remove duplicates while preserving order
        # This handles cases where multiple keywords match the same server
        selected_servers = list(dict.fromkeys(selected_servers))

        # If no servers selected, default to restaurant server
        # This ensures we always have at least one server to work with
        if not selected_servers:
            selected_servers = ["restaurant"]

        return selected_servers


if __name__ == "__main__":
    """
    Test script for the MCPServerSelectorNode
    
    This script demonstrates the selector's capabilities with various query types:
    - Single-domain queries (restaurant, parking, weather)
    - Multi-domain queries (restaurant + parking, restaurant + weather)
    - Complex queries requiring all three servers
    - Edge cases and error handling
    """
    from langchain_groq import ChatGroq

    # Create LLM instance for testing
    llm = ChatGroq(model="qwen-qwq-32b")

    # Create MCPServerSelectorNode instance
    selector = MCPServerSelectorNode(llm)

    # Test with different types of questions to demonstrate various selection patterns
    test_questions = [
        "What restaurants are available?",  # Should select: restaurant
        "Is there parking near the restaurant?",  # Should select: parking
        "What's the weather like today?",  # Should select: weather
        "Find me a restaurant with parking nearby",  # Should select: restaurant, parking
        "I want to find a good sushi restaurant with parking and check the weather",  # Should select: all three
        "Show me restaurants and parking options",  # Should select: restaurant, parking
        "What's the weather like and are there restaurants nearby?",  # Should select: weather, restaurant
        "Find parking and check weather for restaurants",  # Should select: all three
    ]

    for question in test_questions:
        test_state = {"messages": [HumanMessage(content=question)]}
        result = selector.process(test_state)
        print(f"Question: {question}")
        print(f"Selected servers: {result['selected_servers']}")
        print(f"Analysis: {result['analysis']}")
        print("-" * 50)
