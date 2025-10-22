from langgraph.graph import StateGraph
from src.langgraphagenticai.state.state import State
from langgraph.graph import START, END
from src.langgraphagenticai.nodes.restaurant_recommendation_node import (
    RestaurantRecommendationNode,
)


class RestaurantRecommendationGraph:
    """
    Restaurant Recommendation Graph Builder
    """

    def __init__(self, model):
        self.llm = model
        self.graph_builder = StateGraph(State)

    def chatbot_restaurant_recommendation(self):
        """
        Builds a chatbot graph for sushi recommendations with evaluation-based routing.
        """
        self.restaurant_recommendation_node = RestaurantRecommendationNode(self.llm)

        self.graph_builder.add_node(
            "restaurant_node", self.restaurant_recommendation_node.restaurant_node_sync
        )
        self.graph_builder.add_edge(START, "restaurant_node")
        self.graph_builder.add_edge("restaurant_node", END)

        return self.graph_builder.compile()
