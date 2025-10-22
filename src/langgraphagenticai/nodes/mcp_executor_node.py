"""
MCP Executor Node Implementation

This module implements the MCP (Model Context Protocol) executor node that:
1. Connects to selected MCP servers (restaurant, parking, weather)
2. Executes tools from those servers to answer user queries
3. Uses LangGraph's ReAct agent pattern for tool execution
4. Handles both synchronous and asynchronous execution
5. Provides comprehensive error handling and timing information

The executor supports multiple MCP servers running on different ports:
- Restaurant server: http://127.0.0.1:8002/mcp
- Parking server: http://127.0.0.1:8003/mcp
- Weather server: http://127.0.0.1:8004/mcp
"""

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage
import asyncio
from pathlib import Path
import sys
from src.langgraphagenticai.state.state import State
from datetime import datetime
import time

# Setup path resolution for imports
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent
sys.path.append(str(project_root))


class MCPExecutorNode:
    """
    Node to execute selected MCP servers and get responses

    This class handles the execution of MCP (Model Context Protocol) servers
    that provide specialized tools for different domains. It:
    - Connects to multiple MCP servers simultaneously
    - Creates ReAct agents with server-specific tools
    - Executes user queries using the appropriate tools
    - Returns structured responses with timing information
    - Handles errors gracefully with fallback responses
    """

    def __init__(self, model):
        """
        Initialize the MCP executor with language model and server configurations

        Args:
            model: The language model instance for agent creation
        """
        self.llm = model
        # Configuration for available MCP servers
        self.server_configs = {
            "restaurant": {
                "url": "http://127.0.0.1:8002/mcp",
                "transport": "streamable_http",
            },
            "Parking": {
                "url": "http://127.0.0.1:8003/mcp",
                "transport": "streamable_http",
            },
            "Weather": {
                "url": "http://127.0.0.1:8004/mcp",
                "transport": "streamable_http",
            },
        }

    async def execute_mcp_servers(self, state: State) -> dict:
        """
        Execute selected MCP servers and get responses asynchronously

        This is the core method that:
        1. Takes the selected servers from the workflow state
        2. Connects to the appropriate MCP servers
        3. Retrieves available tools from those servers
        4. Creates a ReAct agent with the tools
        5. Executes the user query using the agent
        6. Returns structured response with timing information

        Args:
            state: Workflow state containing selected_servers and user messages

        Returns:
            dict: Response with messages, MCP responses, and timing data
        """
        print("MCPExecutorNode called")

        # Record start time for performance tracking
        start_time = datetime.now()
        start_timestamp = time.time()

        try:
            # Get selected servers from state (default to restaurant if none specified)
            selected_servers = state.get("selected_servers", ["restaurant"])
            print(f"🔧 MCP Executor: Using selected servers: {selected_servers}")

            # Build server configuration for selected servers only
            # This ensures we only connect to servers that are actually needed
            server_config = {}
            for server in selected_servers:
                if server == "restaurant":
                    server_config["restaurant"] = self.server_configs["restaurant"]
                    print("   ✅ Added restaurant server")
                elif server == "parking":
                    server_config["Parking"] = self.server_configs["Parking"]
                    print("   ✅ Added parking server")
                elif server == "weather":
                    server_config["Weather"] = self.server_configs["Weather"]
                    print("   ✅ Added weather server")

            # Handle case where no valid servers were selected
            if not server_config:
                return {
                    "messages": "No valid servers selected",
                    "mcp_responses": {},
                    "start_time": start_time,
                    "end_time": datetime.now(),
                    "response_time_seconds": time.time() - start_timestamp,
                }

            # Create MultiServerMCPClient with selected servers
            # This client can connect to multiple MCP servers simultaneously
            client = MultiServerMCPClient(server_config)

            # Get tools from selected servers
            # These tools will be used by the ReAct agent to answer queries
            tools = await client.get_tools()

            if not tools:
                return {
                    "messages": "No tools available from selected servers",
                    "mcp_responses": {},
                    "start_time": start_time,
                    "end_time": datetime.now(),
                    "response_time_seconds": time.time() - start_timestamp,
                }

            # Create ReAct agent with available tools
            # ReAct (Reasoning + Acting) pattern allows the agent to use tools
            # to reason about and answer complex queries
            agent = create_react_agent(self.llm, tools)

            # Execute the agent with user messages
            # The agent will use the available tools to answer the user's query
            response = await agent.ainvoke({"messages": state["messages"]})

            # Record end time and calculate total execution duration
            end_time = datetime.now()
            end_timestamp = time.time()
            response_time_seconds = end_timestamp - start_timestamp

            # Extract the final response from the agent's execution
            final_message = (
                response["messages"][-1]
                if response["messages"]
                else AIMessage(content="No response generated")
            )

            print("🔍 MCP Executor Debug:")
            print(f"   Selected servers: {selected_servers}")
            print(f"   Tools used: {[tool.name for tool in tools] if tools else []}")
            print(
                f"   Final message: {final_message.content if hasattr(final_message, 'content') else str(final_message)}"
            )

            return {
                "messages": final_message,
                "mcp_responses": {
                    "selected_servers": selected_servers,
                    "tools_used": [tool.name for tool in tools] if tools else [],
                    "response": final_message.content
                    if hasattr(final_message, "content")
                    else str(final_message),
                },
                "start_time": start_time,
                "end_time": end_time,
                "response_time_seconds": response_time_seconds,
            }

        except Exception as e:
            print(f"Error in MCP execution: {e}")
            # Record end time even for errors to maintain timing consistency
            end_time = datetime.now()
            end_timestamp = time.time()
            response_time_seconds = end_timestamp - start_timestamp

            return {
                "messages": AIMessage(content=f"Error executing MCP servers: {str(e)}"),
                "mcp_responses": {"error": str(e)},
                "start_time": start_time,
                "end_time": end_time,
                "response_time_seconds": response_time_seconds,
            }

    def execute_mcp_servers_sync(self, state: State) -> dict:
        """
        Synchronous wrapper for the async MCP execution

        This method provides a synchronous interface to the async MCP execution.
        It's used by the LangGraph workflow which expects synchronous node functions.

        Args:
            state: Workflow state containing selected_servers and user messages

        Returns:
            dict: Response with messages, MCP responses, and timing data
        """
        return asyncio.run(self.execute_mcp_servers(state))
        
if __name__ == "__main__":
    """
    Test script for the MCPExecutorNode
    
    This script demonstrates the executor's capabilities with various server combinations:
    - Single server execution (restaurant, parking)
    - Multi-server execution (restaurant + parking)
    - Error handling for invalid configurations
    """
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage

    # Create LLM instance for testing
    llm = ChatGroq(model="qwen-qwq-32b")

    # Create MCPExecutorNode instance
    executor = MCPExecutorNode(llm)

    # Test with different server combinations to demonstrate various execution paths
    test_cases = [
        {
            "selected_servers": ["restaurant"],
            "messages": [HumanMessage(content="What restaurants are available?")],
        },
        {
            "selected_servers": ["parking"],
            "messages": [HumanMessage(content="Show me parking options")],
        },
        {
            "selected_servers": ["restaurant", "parking"],
            "messages": [HumanMessage(content="Find me a restaurant with parking")],
        },
    ]

    for test_case in test_cases:
        print(f"Testing with servers: {test_case['selected_servers']}")
        result = executor.execute_mcp_servers_sync(test_case)
        print(f"Response: {result['messages']}")
        print("-" * 50)
