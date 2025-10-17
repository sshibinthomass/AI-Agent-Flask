from langgraph.graph import StateGraph
from src.langgraphagenticai.state.state import State
from langgraph.graph import START,END
from src.langgraphagenticai.nodes.basic_chatbot_node import BasicChatbotNode,RestaurantRecommendationNode
import asyncio
from dotenv import load_dotenv
load_dotenv()

class GraphBuilder:
    def __init__(self,model,user_controls_input,message):
        self.llm=model
        self.user_controls_input=user_controls_input
        self.message=message
        self.current_llm=user_controls_input["selected_llm"]
        self.graph_builder=StateGraph(State)  #StateGraph is a class in LangGraph that is used to build the graph

    def basic_chatbot_build_graph(self):
        """
        Builds a basic chatbot graph using LangGraph.
        This method initializes a chatbot node using the `BasicChatbotNode` class 
        and integrates it into the graph. The chatbot node is set as both the 
        entry and exit point of the graph.
        """
        self.basic_chatbot_node=BasicChatbotNode(self.llm)

        self.graph_builder.add_node("chatbot",self.basic_chatbot_node.process)
        self.graph_builder.add_edge(START,"chatbot")
        self.graph_builder.add_edge("chatbot",END)
    
    def chatbot_restaurant_recommendation(self):
        """
        Builds a chatbot graph for sushi recommendations with evaluation-based routing.
        """
        self.restaurant_recommendation_node = RestaurantRecommendationNode(self.llm)

        self.graph_builder.add_node("restaurant_node", self.restaurant_recommendation_node.restaurant_node_sync)
        self.graph_builder.add_edge(START, "restaurant_node")
        self.graph_builder.add_edge("restaurant_node", END)
        

    def assistant_chatbot_build_graph(self):
        """
        Builds a assistant chatbot graph using LangGraph.
        """
        self.restaurant_recommendation_node = RestaurantRecommendationNode(self.llm)

        self.graph_builder.add_node("chatbot", self.restaurant_recommendation_node.process_sync)
        self.graph_builder.add_node("evaluate_node", self.restaurant_recommendation_node.evaluate_node)
        self.graph_builder.add_node("store_node", self.restaurant_recommendation_node.store_node)
        self.graph_builder.add_node("search_node", self.restaurant_recommendation_node.search_node)

        self.graph_builder.add_edge(START, "chatbot")
        self.graph_builder.add_edge("chatbot", "evaluate_node")

        # Conditional routing based on evaluate_node's result
        def route_after_evaluate(state):
            # The evaluate_node returns {"result": True} or {"result": False}
            result = state.get("result", False)
            if result:
                return "store_node"
            else:
                return "search_node"

        self.graph_builder.add_conditional_edges(
            "evaluate_node",
            route_after_evaluate,
            {
                "store_node": "store_node",
                "search_node": "search_node"
            }
        )
        self.graph_builder.add_edge("search_node", "store_node")
        self.graph_builder.add_edge("store_node", END)


    def setup_graph(self,usecase:str):
        """
        Sets up the graph for the selected use case.
        """

        if usecase == "Sushi":
           self.chatbot_restaurant_recommendation()
        elif usecase == "Agentic AI":
           self.assistant_chatbot_build_graph()
        else:
           self.basic_chatbot_build_graph()

        return self.graph_builder.compile()
