from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import os
import sys
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import asyncio #asyncio is a library for asynchronous programming in Python.
from pathlib import Path
#from langchain_community.embeddings import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings
from tavily import TavilyClient
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime

current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent
sys.path.append(str(project_root))
from src.langgraphagenticai.state.state import State
load_dotenv()
os.environ["GROQ_API_KEY"]=os.getenv("GROQ_API_KEY")
os.environ["GEMINI_API_KEY"]=os.getenv("GEMINI_API_KEY")

class StorageDecision(BaseModel):
    should_store: bool = Field(description="Whether to store the information - true or false")
    message_to_store: str = Field(description="The clean, concise message to store (empty if not storing)")
    reason: str = Field(description="Reason for the storage decision")
    is_duplicate: bool = Field(description="Whether this information is similar to existing stored information")


class BasicChatbotNode:
    """
    Basic Chatbot login implementation
    """
    def __init__(self,model):
        self.llm=model

    def process(self,state:State)->dict:
        """
        Processes the input state and generates a chatbot response.
        """
        response = self.llm.invoke(state['messages'])
    
    #Error handling for the response 
        # If response is an AIMessage, extract .content
        if hasattr(response, "content"):
            return {"messages": response.content}
        # If response is a dict with 'content', extract it
        if isinstance(response, dict) and 'content' in response:
            return {"messages": response['content']}
        # If response is a string, return as is
        return {"messages": response}

class RestaurantRecommendationNode:
    """
    Restaurant Recommendation Node  
    """
    def __init__(self,model):
        self.llm=model

    def retrieve_node(self,state:State)->dict:
        """
        Processes the input state and retrieves information from the long term memory.
        """
        #print(state)
        messages = state["messages"]
        if not messages:
            return {"messages": "No messages to process"}
        
        # Get the last message content
        last_message = messages[-2]
        if hasattr(last_message, 'content'):
            user_input = last_message.content
        elif isinstance(last_message, dict) and 'content' in last_message:
            user_input = last_message['content']
        else:
            user_input = str(last_message)
        embedding=OpenAIEmbeddings()
        db = Chroma(persist_directory="./chroma_openai", embedding_function=embedding)
        docs=db.similarity_search(user_input)
        retrieved_info = "\n".join([f"Document: {doc.page_content}" for doc in docs])
        return {"retrieved_info": retrieved_info}

    async def process(self,state:State)->dict:
        """
        Processes the input state and generates a chatbot response.
        """
        print("Chatbot_node called")
        try:
            #MultiServerMCPClient is a client that can connect to multiple MCP servers.
            client=MultiServerMCPClient( 
                {
                    "restaurant":{
                        "url": "http://127.0.0.1:8002/mcp", 
                        "transport": "streamable_http",
                    },
                    "Parking":{
                        "url": "http://127.0.0.1:8003/mcp", 
                        "transport": "streamable_http",
                    }
                }
            )
            
            tools=await client.get_tools()
            model=self.llm
            agent=create_react_agent(
                model, tools
            )
            #print(state['messages'])
            retrieved_info=self.retrieve_node(state)
            rag_system_message = SystemMessage(
                content=f"Relevant information retrieved for this query based on personal information:\n\n{retrieved_info}"
            )
            base_system_msg = state["messages"][0]
            conversation = state["messages"][1:]
            messages = [base_system_msg, rag_system_message] + conversation
            response = await agent.ainvoke(
                {"messages": messages}
            )
        except Exception as e:
            print(e)
            return {"messages": "Error: " + str(e)}
        return {"messages": AIMessage(content=response['messages'][-1].content)}
    
    #When called async directly from graph builter it gave error so added a sync function which calls the asyncio function
    def process_sync(self, state: State) -> dict:
        """
        Processes the input state and generates a chatbot response.
        """
        return asyncio.run(self.process(state))
    

    def store_node(self,state:State)->dict:
        """
        Processes the input state and decides whether to store information in a single LLM call.
        """
        print("store_node called")
        # Extract the last user message content from the messages list
        messages = state["messages"]
        #print(messages)
        if not messages:
            return {"messages": "No messages to process"}
        
        # Get the last message content
        last_message = messages[-2]
        if hasattr(last_message, 'content'):
            user_input = last_message.content
        elif isinstance(last_message, dict) and 'content' in last_message:
            user_input = last_message['content']
        else:
            user_input = str(last_message)
        embedding=OpenAIEmbeddings()
        
        retrieved_info=self.retrieve_node(state)
        # Single LLM call to make all decisions
        llm_with_structured = self.llm.with_structured_output(StorageDecision)
        response = llm_with_structured.invoke([
            SystemMessage(content="""
                You are a helpful assistant that decides whether to store user information.
                
                Rules:
                1. Store information if it contains personal details (name, age, location, contact info) or preferences (likes/dislikes)
                2. Do NOT store if the information is too similar to existing stored information
                3. Do NOT store general questions, weather queries, or non-personal information
                4. Create a clean, concise version for storage that's easy to retrieve
                
                Return:
                - should_store: true only if information should be stored AND is not duplicate
                - message_to_store: clean version of the information (empty if not storing)
                - reason: explanation of your decision
                - is_duplicate: true if information is too similar to existing data
                """),
            HumanMessage(content=f"""
                User input: {user_input}
                Retrieved information: {retrieved_info}
                
                Should I store this information?
                """)
        ])
        
        # Store if decision is to store
        if response.should_store and response.message_to_store:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
            splits = text_splitter.split_text(response.message_to_store)
            vectordb=Chroma.from_texts(texts=splits,embedding=embedding,persist_directory="./chroma_openai")
        
        result={
            "stored": response.should_store,
            "reason": response.reason,
            "is_duplicate": response.is_duplicate,
            "message_to_store": response.message_to_store,
        }
        print(result)
        print("--------------------------------")
        return result

    def evaluate_node(self, state: State) -> dict:
        """
        Evaluates if the last AI answer is relevant and not an 'I don't know' response.
        Returns {"result": True} if relevant, {"result": False} otherwise.
        """
        print("evaluate_node called")
        class EvaluationResult(BaseModel):
            result: bool = Field(description="True if the answer is relevant and not an 'I don't know' response, False otherwise.")

        messages = state["messages"]
        if not messages:
            return {"result": False}

        # Find the last HumanMessage and last AIMessage
        last_human = None
        last_ai = None
        for msg in reversed(messages):
            if last_ai is None and isinstance(msg, AIMessage):
                last_ai = msg
            elif last_human is None and isinstance(msg, HumanMessage):
                last_human = msg
            if last_ai and last_human:
                break

        if not last_human or not last_ai:
            return {"result": False}

        # Use the LLM to check if the answer is relevant and not an "I don't know" response
        prompt = (
            "You are an evaluator. Given the user's question and the assistant's answer, "
            "determine if the answer is relevant and does not say 'I don't know' or similar. "
            "If the answer is relevant and correct, respond with result: true. "
            "If the answer is irrelevant or says it doesn't know, respond with result: false.\n\n"
            f"User question: {last_human.content}\n"
            f"Assistant answer: {last_ai.content}\n"
            "Is the answer relevant and not an 'I don't know' response? (result: true/false):"
        )

        llm_with_structured = self.llm.with_structured_output(EvaluationResult)
        result = llm_with_structured.invoke(prompt)

        # result is an EvaluationResult instance
        return {"result": result.result}

    def search_node(self, state: State) -> dict:
        """
        Processes the input state and searches for information in the long term memory.
        Removes the last AIMessage from the messages, uses the last HumanMessage as the query,
        and returns the result in the same format as the process node.
        """
        print("search_node called")
        tavily = TavilyClient()
        model = self.llm

        # Copy messages to avoid mutating the original state
        messages = state["messages"].copy()

        # Remove the last AIMessage (assistant) from the messages
        for i in range(len(messages) - 1, -1, -1):
            if isinstance(messages[i], AIMessage):
                del messages[i]
                break

        # Separate last HumanMessage (current user question) and previous chat history
        last_human = None
        history_messages = []
        for msg in reversed(messages):
            if last_human is None and isinstance(msg, HumanMessage):
                last_human = msg
            else:
                history_messages.append(msg)
        history_messages = list(reversed(history_messages))  # restore original order

        # Prepare chat history string (excluding system messages for brevity, or include as needed)
        chat_history = []
        for msg in history_messages:
            if isinstance(msg, HumanMessage):
                chat_history.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                chat_history.append(f"Assistant: {msg.content}")
        chat_history_str = "\n".join(chat_history)

        if not last_human:
            return {"messages": "No user message found for search."}
        now = datetime.now()
        # Ask the LLM to generate a context-rich search query for Tavily
        query_generation_prompt = (
            "Given the following chat history and the user's current question, generate a concise search query that captures all necessary context "
            "for the user's latest question. The query should be suitable for a web search engine and should resolve any references or pronouns.\n\n"
            f"Chat history:\n{chat_history_str}\n\n"
            f"Current user question: {last_human.content}\n\n"
            f"Current date and time: {now}\n\n"
            "Search query:"
        )
        search_query_result = self.llm.invoke(query_generation_prompt)
        if hasattr(search_query_result, "content"):
            search_query = search_query_result.content.strip()
        elif isinstance(search_query_result, dict) and "content" in search_query_result:
            search_query = search_query_result["content"].strip()
        else:
            search_query = str(search_query_result).strip()
        print("search_query-",search_query)
        # Now use the generated query for Tavily
        tavily_results = tavily.search(query=search_query).get('results', [])

        # Prepare articles string for the LLM
        articles_str = "\n\n".join([
            f"Content: {item.get('content', '')}\nURL: {item.get('url', '')}\nDate: {item.get('published_date', '')}"
            for item in tavily_results
        ])

        # Prepare chat history (excluding system messages for brevity, or include as needed)
        chat_history = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                chat_history.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                chat_history.append(f"Assistant: {msg.content}")

        chat_history_str = "\n".join(chat_history)

        # Conversational prompt with chat history and search results
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant. Use the following chat history and search results to answer the user's latest question in a conversational, concise, and relevant way. If the results are not helpful, say you don't know."),
            ("user", "Chat history:\n{chat_history}\n\nSearch results:\n{articles}\n\nPlease answer the user's last question based on these results.")
        ])

        # Get the LLM's answer
        llm_response = self.llm.invoke(prompt_template.format(
            chat_history=chat_history_str,
            articles=articles_str
        ))
        #print(llm_response)
        # Return in the same format as process node
        if hasattr(llm_response, "content"):
            return {"messages": llm_response.content}
        elif isinstance(llm_response, dict) and 'content' in llm_response:
            return {"messages": llm_response['content']}
        else:
            return {"messages": str(llm_response)}

    async def restaurant_node(self,state:State)->dict:
        """
        Processes the input state and generates a chatbot response.
        """
        print("restaurant_node called")
        try:
            #MultiServerMCPClient is a client that can connect to multiple MCP servers.
            client=MultiServerMCPClient( 
                {
                    "restaurant":{
                        "url": "http://127.0.0.1:8002/mcp", 
                        "transport": "streamable_http",
                    },
                    "Parking":{
                        "url": "http://127.0.0.1:8003/mcp", 
                        "transport": "streamable_http",
                    }
                }
            )
            
            tools=await client.get_tools()
            model=self.llm
            agent=create_react_agent(
                model, tools
            )

            response = await agent.ainvoke(
                {"messages": state["messages"]}
            )
        except Exception as e:
            print(e)
            return {"messages": "Error: " + str(e)}
        return {"messages": AIMessage(content=response['messages'][-1].content)}
    
    #When called async directly from graph builter it gave error so added a sync function which calls the asyncio function
    def restaurant_node_sync(self, state: State) -> dict:
        """
        Processes the input state and generates a chatbot response.
        """
        return asyncio.run(self.restaurant_node(state))


if __name__ == "__main__":
    

    # Create LLM instance
    llm = ChatGroq(model="qwen-qwq-32b")
    
    # Create RestaurantRecommendationNode instance with the LLM
    node = RestaurantRecommendationNode(llm)
    
    # Example conversation history
    search_state = {
        "messages": [
            SystemMessage(content="You are a helpful and efficient assistant. You help the user find the best sushi restaurants in Munich using up-to-date weather information and Google reviews. You also help the user find the best parking spots in Munich, considering current conditions. Always provide accurate, relevant, and concise recommendations."),
            HumanMessage(content="Hi"),
            AIMessage(content="Hello, I'm here to help. How can I assist you today? Are you looking for recommendations on sushi restaurants in Munich or perhaps assistance with finding a parking spot?"),
            HumanMessage(content="Yes, what are the available restaurants?"),
            AIMessage(content="Here are some sushi restaurants in Munich:\n\n1. Sasou - Address: Marienplatz 28, 80331 Munich, Food Types: Japanese - Sushi, Asian, Japanese, Southeast Asian, German, Fast Food, Soup, Price Level: 3 out of 5\n2. Galeria Restaurant - Address: Kaufingerstraße 1, 80331 Munich, Food Types: Japanese - Sushi, European, German, Price Level: 1 out of 5\n3. Shaokao Asian Grill&Wine - Address: Fürstenfelder Straße 9, 80331 Munich, Food Types: Japanese - Sushi, Asian, Chinese, Japanese, European, International, Fusion, Grill, Price Level: Unknown\n4. Secret Garden - Address: Heiliggeiststraße 2A, 80331 Munich, Food Types: Japanese - Sushi, Asian, Vietnamese, Vegan, Price Level: Unknown\n\nLet me know if you need more information or if you'd like to get reviews for any of these restaurants."),
            HumanMessage(content="Can you give google reviews for Galeria Restaurant"),
            AIMessage(content="The Galeria Restaurant has an average rating of 3.7 out of 5 based on 63 Google reviews. The restaurant offers a wide variety of food, including sushi, and has a comfortable seating area with a view of the church. However, some reviewers have mentioned that the food can be expensive, especially when buying by weight, and that the labeling of food items can be unclear. The staff has also been described as unfriendly and rude by some reviewers. Overall, the restaurant seems to be a good option for those looking for a variety of food options in a convenient location, but may not be the best choice for those on a budget or with specific dietary restrictions."),
            HumanMessage(content="What does people tell about reviews?"),
            AIMessage(content="Based on the Google reviews, people have mixed opinions about the Galeria Restaurant. Some reviewers have praised the restaurant's variety of food, comfortable seating, and convenient location. However, others have mentioned that the food can be expensive, especially when buying by weight, and that the labeling of food items can be unclear. Some reviewers have also described the staff as unfriendly and rude. Overall, the restaurant seems to be a good option for those looking for a variety of food options in a convenient location, but may not be the best choice for those on a budget or with specific dietary restrictions."),
        ]
    }

    # Call the search_node method and print the result
    search_result = node.evaluate_node(search_state)
    print("Search Node Result:", search_result)
