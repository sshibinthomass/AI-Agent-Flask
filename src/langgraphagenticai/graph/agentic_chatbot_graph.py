"""
Agentic Chatbot Graph Implementation

This module implements a sophisticated agentic chatbot system using LangGraph that can:
1. Dynamically select appropriate MCP (Model Context Protocol) servers based on user queries
2. Execute selected MCP servers to gather relevant information
3. Fall back to basic chatbot functionality when MCP servers aren't needed
4. Merge and format responses from multiple sources

The graph follows a workflow pattern:
User Query → MCP Selection → MCP Execution (if needed) → Response Merging → Final Response
"""

from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage, HumanMessage
from pathlib import Path
import sys
from src.langgraphagenticai.state.state import State
from src.langgraphagenticai.nodes.mcp_selector_node import MCPServerSelectorNode
from src.langgraphagenticai.nodes.mcp_executor_node import MCPExecutorNode
from src.langgraphagenticai.nodes.basic_chatbot_node import BasicChatbotNode
from datetime import datetime
import time

# Setup path resolution for imports
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent
sys.path.append(str(project_root))


class AgenticChatbotGraph:
    """
    Agentic Chatbot Graph that dynamically selects and executes MCP servers

    This class orchestrates a sophisticated chatbot workflow that can:
    - Analyze user queries to determine which MCP servers are needed
    - Execute multiple MCP servers in parallel when appropriate
    - Fall back to basic chatbot functionality for general queries
    - Merge responses from multiple sources into coherent answers

    The graph uses LangGraph's StateGraph to manage the workflow state and
    conditional routing between different processing nodes.
    """

    def __init__(self, model):
        """
        Initialize the agentic chatbot graph with required components

        Args:
            model: The language model instance (e.g., ChatGroq, ChatOpenAI)
        """
        self.model = model
        # Initialize specialized nodes for different processing stages
        self.selector_node = MCPServerSelectorNode(
            model
        )  # Analyzes queries and selects MCP servers
        self.executor_node = MCPExecutorNode(model)  # Executes selected MCP servers
        self.basic_chatbot = BasicChatbotNode(model)  # Fallback for general queries
        self.graph = self._build_graph()  # Build the workflow graph

    def _build_graph(self) -> StateGraph:
        """
        Build the agentic chatbot graph with dynamic MCP server selection

        Creates a LangGraph StateGraph with the following workflow:
        1. mcp_selector: Analyzes user query and determines which MCP servers to use
        2. Conditional routing: Either use MCP servers or fallback chatbot
        3. mcp_executor: Executes selected MCP servers (if needed)
        4. fallback_chatbot: Handles general queries without MCP servers
        5. response_merger: Combines and formats the final response

        Returns:
            StateGraph: Compiled workflow graph ready for execution
        """
        # Create the state graph with our custom State class
        workflow = StateGraph(State)

        # Add processing nodes to the workflow
        workflow.add_node(
            "mcp_selector", self._mcp_selector_node
        )  # Analyzes queries and selects servers
        workflow.add_node(
            "mcp_executor", self._mcp_executor_node
        )  # Executes selected MCP servers
        workflow.add_node(
            "response_merger", self._response_merger_node
        )  # Merges and formats responses
        workflow.add_node(
            "fallback_chatbot", self._fallback_chatbot_node
        )  # Handles general queries

        # Set the entry point - all queries start with MCP selection
        workflow.set_entry_point("mcp_selector")

        # Add conditional routing based on whether MCP servers are needed
        workflow.add_conditional_edges(
            "mcp_selector",
            self._should_use_mcp,  # Decision function
            {
                "use_mcp": "mcp_executor",  # Route to MCP execution if servers selected
                "use_fallback": "fallback_chatbot",  # Route to basic chatbot if no servers needed
            },
        )

        # Both execution paths lead to response merger
        workflow.add_edge("mcp_executor", "response_merger")  # MCP path
        workflow.add_edge("fallback_chatbot", "response_merger")  # Fallback path
        workflow.add_edge("response_merger", END)  # End the workflow

        return workflow.compile()

    def _mcp_selector_node(self, state: State) -> dict:
        """
        Node to select appropriate MCP servers based on user query

        This node analyzes the user's message and determines which MCP servers
        would be most relevant for answering their question. It uses an LLM to
        intelligently parse the query and select from available servers:
        - restaurant: For food, dining, menu queries
        - parking: For parking availability and location queries
        - weather: For weather and climate queries

        Args:
            state: Current workflow state containing user messages

        Returns:
            dict: Updated state with selected_servers and analysis
        """
        print(f"🔍 Graph MCP Selector - Input state keys: {list(state.keys())}")
        result = self.selector_node.process(state)
        print(f"🔍 Graph MCP Selector - Output keys: {list(result.keys())}")
        return result

    def _mcp_executor_node(self, state: State) -> dict:
        """
        Node to execute selected MCP servers and gather information

        This node takes the selected MCP servers from the selector and executes
        them to gather relevant information. It:
        1. Connects to the selected MCP servers (restaurant, parking, weather)
        2. Uses the servers' tools to answer the user's query
        3. Returns structured responses with timing information

        Args:
            state: Current workflow state with selected_servers and user messages

        Returns:
            dict: Updated state with MCP responses and execution details
        """
        print(f"🔍 Graph MCP Executor - Input state keys: {list(state.keys())}")
        print(
            f"🔍 Graph MCP Executor - Selected servers: {state.get('selected_servers')}"
        )
        result = self.executor_node.execute_mcp_servers_sync(state)
        print(f"🔍 Graph MCP Executor - Output keys: {list(result.keys())}")
        return result

    def _fallback_chatbot_node(self, state: State) -> dict:
        """
        Fallback to basic chatbot when MCP servers are not needed

        This node handles general queries that don't require specialized MCP servers.
        It provides standard conversational AI responses for questions like:
        - General greetings and small talk
        - Questions not related to restaurants, parking, or weather
        - Complex queries that don't fit the MCP server categories

        Args:
            state: Current workflow state with user messages

        Returns:
            dict: Updated state with basic chatbot response
        """
        return self.basic_chatbot.process(state)

    def _response_merger_node(self, state: State) -> dict:
        """
        Merge and format the final response from all processing paths

        This node is the final step in the workflow that:
        1. Extracts the response content from the state
        2. Handles both MCP-generated responses and basic chatbot responses
        3. Formats the final message for the user
        4. Records timing information for performance monitoring
        5. Provides error handling for response generation failures

        Args:
            state: Current workflow state containing messages, MCP responses, and metadata

        Returns:
            dict: Final state with formatted response and timing information
        """
        # Record start time for performance tracking
        start_time = datetime.now()
        start_timestamp = time.time()

        try:
            # Extract response components from state
            messages = state.get("messages", "")
            mcp_responses = state.get("mcp_responses", {})
            selected_servers = state.get("selected_servers", [])

            print("🔍 Response Merger Debug:")
            print(f"   Selected servers: {selected_servers}")
            print(f"   MCP responses: {mcp_responses}")
            print(f"   Messages type: {type(messages)}")
            print(f"   Messages content: {messages}")

            # Extract the actual content from messages (handle different message formats)
            if isinstance(messages, list) and len(messages) > 0:
                # Get the last message content from the conversation
                last_message = messages[-1]
                if hasattr(last_message, "content"):
                    response_content = last_message.content
                elif isinstance(last_message, dict) and "content" in last_message:
                    response_content = last_message["content"]
                else:
                    response_content = str(last_message)
            elif isinstance(messages, str):
                response_content = messages
            else:
                response_content = str(messages)

            # Create the final response message
            if mcp_responses and not mcp_responses.get("error"):
                # MCP response was successful - use the MCP-generated content
                # Note: Server attribution is commented out but could be re-enabled
                # if selected_servers:
                #    server_info = f"\n\n[Information gathered from: {', '.join(selected_servers)} servers]"
                #    response_content += server_info

                final_message = AIMessage(content=response_content)
            else:
                # Use basic chatbot response (fallback path)
                final_message = AIMessage(content=response_content)

            # Record end time and calculate total response duration
            end_time = datetime.now()
            end_timestamp = time.time()
            response_time_seconds = end_timestamp - start_timestamp

            return {
                "messages": final_message,
                "start_time": start_time,
                "end_time": end_time,
                "response_time_seconds": response_time_seconds,
            }

        except Exception as e:
            # Handle any errors in response merging gracefully
            # Record end time even for errors to maintain timing consistency
            end_time = datetime.now()
            end_timestamp = time.time()
            response_time_seconds = end_timestamp - start_timestamp

            return {
                "messages": AIMessage(content=f"Error merging response: {str(e)}"),
                "start_time": start_time,
                "end_time": end_time,
                "response_time_seconds": response_time_seconds,
            }

    def _should_use_mcp(self, state: State) -> str:
        """
        Determine whether to use MCP servers or fallback to basic chatbot

        This is the decision function for conditional routing in the workflow.
        It examines the selected_servers from the MCP selector to determine
        the appropriate execution path:
        - If servers were selected → use MCP execution path
        - If no servers selected → use basic chatbot fallback path

        Args:
            state: Current workflow state containing selected_servers

        Returns:
            str: Routing decision ("use_mcp" or "use_fallback")
        """
        selected_servers = state.get("selected_servers", [])

        # Use MCP execution path if we have valid servers selected
        if selected_servers and len(selected_servers) > 0:
            return "use_mcp"
        else:
            # Use basic chatbot for general queries
            return "use_fallback"

    def invoke(self, state: State) -> dict:
        """
        Invoke the agentic chatbot graph with synchronous execution

        This is the main entry point for processing user queries through the
        complete workflow. It executes the entire graph and returns the final
        response with timing information.

        Args:
            state: Initial state containing user messages

        Returns:
            dict: Final state with response, timing, and metadata
        """
        try:
            result = self.graph.invoke(state)
            return result
        except Exception as e:
            return {
                "messages": AIMessage(content=f"Error in agentic chatbot: {str(e)}"),
                "error": str(e),
            }

    def stream(self, state: State):
        """
        Stream the agentic chatbot graph execution for real-time processing

        This method provides streaming execution of the workflow, yielding
        intermediate results as each node completes. Useful for:
        - Real-time user feedback
        - Progress monitoring
        - Debugging workflow execution
        - Building interactive interfaces

        Args:
            state: Initial state containing user messages

        Yields:
            dict: Intermediate state updates from each workflow node
        """
        try:
            for chunk in self.graph.stream(state):
                yield chunk
        except Exception as e:
            yield {
                "messages": AIMessage(content=f"Error in agentic chatbot: {str(e)}"),
                "error": str(e),
            }


if __name__ == "__main__":
    """
    Test script for the AgenticChatbotGraph
    
    This script demonstrates the graph's capabilities with various query types:
    - Restaurant queries (should use restaurant MCP server)
    - Parking queries (should use parking MCP server)  
    - Weather queries (should use weather MCP server)
    - Multi-domain queries (should use multiple MCP servers)
    - General queries (should use fallback chatbot)
    """
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage

    # Create LLM instance for testing
    llm = ChatGroq(model="qwen-qwq-32b")

    # Create AgenticChatbotGraph instance
    agentic_chatbot = AgenticChatbotGraph(llm)

    # Test with different types of questions to demonstrate various execution paths
    test_questions = [
        "What restaurants are available?",  # Should use restaurant MCP server
        "Is there parking near restaurants?",  # Should use parking MCP server
        "What's the weather like?",  # Should use weather MCP server
        "Find me a restaurant with parking and check the weather",  # Should use multiple MCP servers
        "Hello, how are you?",  # Should use fallback chatbot
    ]

    for question in test_questions:
        print(f"\n{'=' * 60}")
        print(f"Question: {question}")
        print("=" * 60)

        test_state = {"messages": [HumanMessage(content=question)]}
        result = agentic_chatbot.invoke(test_state)

        print(f"Response: {result.get('messages', 'No response')}")
        if "selected_servers" in result:
            print(f"Servers used: {result['selected_servers']}")
        if "mcp_responses" in result:
            print(f"MCP responses: {result['mcp_responses']}")
