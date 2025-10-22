from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage
import asyncio
from pathlib import Path
import sys
from src.langgraphagenticai.state.state import State
from datetime import datetime
import time

current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent
sys.path.append(str(project_root))


class RestaurantRecommendationNode:
    """
    Restaurant Recommendation Node
    """

    def __init__(self, model):
        self.llm = model

    async def restaurant_node(self, state: State) -> dict:
        """
        Processes the input state and generates a chatbot response.
        """
        print("restaurant_node called")

        # Record start time
        start_time = datetime.now()
        start_timestamp = time.time()

        try:
            # MultiServerMCPClient is a client that can connect to multiple MCP servers.
            client = MultiServerMCPClient(
                {
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
            )

            tools = await client.get_tools()
            model = self.llm
            agent = create_react_agent(model, tools)

            response = await agent.ainvoke({"messages": state["messages"]})

            # Record end time and calculate duration
            end_time = datetime.now()
            end_timestamp = time.time()
            response_time_seconds = end_timestamp - start_timestamp

            return {
                "messages": AIMessage(content=response["messages"][-1].content),
                "start_time": start_time,
                "end_time": end_time,
                "response_time_seconds": response_time_seconds,
            }
        except Exception as e:
            print(e)
            # Record end time even for errors
            end_time = datetime.now()
            end_timestamp = time.time()
            response_time_seconds = end_timestamp - start_timestamp

            return {
                "messages": "Error: " + str(e),
                "start_time": start_time,
                "end_time": end_time,
                "response_time_seconds": response_time_seconds,
            }

    # When called async directly from graph builter it gave error so added a sync function which calls the asyncio function
    def restaurant_node_sync(self, state: State) -> dict:
        """
        Processes the input state and generates a chatbot response.
        """
        return asyncio.run(self.restaurant_node(state))
