from typing_extensions import TypedDict, List
from langgraph.graph.message import add_messages
from typing import Annotated, Optional
from datetime import datetime


class State(TypedDict):
    """
    Represent the structure of the state used in graph,
    add_messages is a function that adds messages to the state for history of the conversation
    """

    messages: Annotated[List, add_messages]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    response_time_seconds: Optional[float]
    selected_servers: Optional[List[str]]
    mcp_responses: Optional[dict]
    analysis: Optional[str]
