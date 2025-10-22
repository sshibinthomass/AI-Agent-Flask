from langgraph.graph import StateGraph
from src.langgraphagenticai.state.state import State
from langgraph.graph import START, END
from src.langgraphagenticai.nodes.test_mcp_node import (
    TestMCPNode,
)


class TestMCPGraph:
    """
    Test MCP Graph Builder
    """

    def __init__(self, model):
        self.llm = model
        self.graph_builder = StateGraph(State)

    def test_mcp_graph(self):
        """
        Builds a test MCP graph.
        """
        self.test_mcp_node = TestMCPNode(self.llm)

        self.graph_builder.add_node(
            "test_mcp_node", self.test_mcp_node.test_mcp_node_sync
        )
        self.graph_builder.add_edge(START, "test_mcp_node")
        self.graph_builder.add_edge("test_mcp_node", END)

        return self.graph_builder.compile()
