# Munich Sushi Chatbot – Project Overview

## Introduction

The Munich Sushi Chatbot is an AI-powered agent designed to assist users in discovering sushi restaurants in Munich and finding suitable parking options nearby. The system leverages advanced language models, real-time data integration, and a modular architecture to provide up-to-date, context-aware recommendations, reviews, and logistical information.

---

## Feature

### 1. Sushi Restaurant Discovery
- **Restaurant Listings:** Provides a curated list of sushi restaurants in Munich, including names, addresses, cuisine types, and price levels.
- **Menu Information:** Displays detailed menu items and prices for each restaurant.
- **Contact Details:** Supplies phone numbers, emails, and website links for direct communication.
- **Google Reviews:** Fetches and summarizes the latest Google reviews for each restaurant.
- **Nearby Restaurants:** Suggests alternative or similar restaurants within a specified radius.

### 2. Parking Assistance
- **Parking Availability:** Shows real-time availability of parking spots near selected restaurants.
- **Open Parking Lots:** Lists currently open parking facilities, including distance, price, and free spot count.
- **24-Hour Parking:** Identifies parking lots open around the clock.
- **Disabled Access:** Highlights parking options with disabled access.
- **Payment Methods:** Details accepted payment methods for each parking lot.

### 3. Additional Contextual Information
- **Weather Integration:** Provides current weather conditions at or near the restaurant location.
- **User-Friendly Chatbot:** Engages in natural conversation, answering queries about restaurants, parking, and related topics.

---

## Technology Stack

### 1. Programming Language
- **Python 3.10+**: The core application and all supporting scripts are written in Python.

### 2. Frameworks & Libraries
- **LangGraph**: For agentic workflow orchestration and state management.
- **Streamlit**: For building the interactive user interface.
- **FastMCP**: For modular tool server/client communication (Multi-Component Protocol).
- **OpenAI, Groq, Gemini, Ollama**: For integrating various LLMs (Large Language Models).
- **Google Maps API**: For restaurant and parking location data, reviews, and place details.
- **Open-Meteo API**: For real-time weather data.
- **dotenv**: For environment variable management.
- **Requests**: For HTTP requests to external APIs.
- **JSON**: For structured data storage and retrieval.

### 3. Data Sources
- **Local JSON Files**: `data/sushi.json` and `data/parking.json` store restaurant and parking data, respectively.
- **Google Maps API**: For live reviews and place details.
- **Open-Meteo API**: For weather updates.

---

## Architecture & Implementation

### 1. Modular Tool Servers (MCP)
- **mcp_parking.py**: Exposes parking-related tools (availability, open lots, 24-hour lots, disabled access, payment methods) via FastMCP on port 8003.
- **mcp_restaurant.py**: Exposes restaurant-related tools (listing, details, reviews, contact info, nearby search) via FastMCP on port 8002.
- **mcp_tools.py**: Aggregates tools for restaurant, parking, weather, and reviews for unified access.

### 2. Orchestration & Agent Logic
- **Orchestrator**: Coordinates tool usage and LLM calls to generate structured, context-aware responses and reports.
- **Nodes**: Specialized classes (e.g., `RestaurantRecommendationNode`) process user queries, retrieve relevant data, and invoke LLMs for response generation.
- **MultiServerMCPClient**: Connects to multiple MCP tool servers, enabling the agent to access both restaurant and parking data seamlessly.

### 3. Data Flow
- **User Query** → **UI (Streamlit)** → **Agent Node** → **MCP Tool Server** → **Data Source/API** → **Response**
- The agent uses RAG (Retrieval-Augmented Generation) to combine LLM output with up-to-date data from local files and APIs.

### 4. User Interface
- **Streamlit App**: Provides an interactive web interface for users to chat with the agent, view restaurant and parking options, and receive recommendations in real time.
- **Configurable UI**: Settings and appearance are managed via `uiconfigfile.ini` and `uiconfigfile.py`.

---

## Graphs and Nodes: Workflow Orchestration

The application leverages the LangGraph framework to model its conversational and data-processing workflow as a directed graph. This approach enables modular, flexible, and maintainable orchestration of complex agentic behaviors.

### Graph Structure
- **StateGraph:** The core workflow is built using `StateGraph`, which defines the flow of data and control between nodes (processing units) in the system.
- **Start and End Nodes:** Each graph has a defined entry (`START`) and exit (`END`) point, ensuring a clear flow from user input to final response.
- **Conditional Edges:** The graph can route data between nodes based on dynamic conditions, enabling evaluation and fallback logic.

### Node Types
Nodes are modular processing units, each responsible for a specific function in the workflow. Key node types include:

- **Chatbot Node (`BasicChatbotNode`):** Handles general conversational logic, processes user queries, and generates responses using the selected LLM.
- **Restaurant Recommendation Node (`RestaurantRecommendationNode`):** Specialized for restaurant-related queries, integrating retrieval-augmented generation (RAG) and tool usage for up-to-date recommendations.
- **Evaluation Node:** Assesses the relevance and quality of the AI's response, determining if further action (e.g., additional search or storage) is needed.
- **Store Node:** Decides whether to store new information in the system's memory, based on deduplication and relevance checks.
- **Search Node:** Triggers additional retrieval or search actions if the initial response is insufficient.
- **Orchestrator Node:** Plans and coordinates the generation of structured reports, breaking down tasks into sections and assigning them to worker nodes.
- **LLM Call Node:** Executes the actual language model call to generate a section of a report or a detailed response.
- **Synthesizer Node:** Aggregates and synthesizes results from multiple worker nodes.
- **Export Markdown Node:** Handles exporting the final report or response to a markdown file.

### Example Graph Workflows
- **Basic Chatbot Graph:**
  - `START` → `chatbot` → `END`
- **Restaurant Recommendation Graph:**
  - `START` → `restaurant_node` → `END`
- **Assistant Chatbot Graph (with evaluation and storage):**
  - `START` → `chatbot` → `evaluate_node` → (conditional: `store_node` or `search_node`) → `store_node` → `END`
- **Report Generation Graph:**
  - `START` → `orchestrator` → (parallel: multiple `llm_call` nodes) → `synthesizer` → `export_markdown` → `END`

### Graph Building and Extensibility
- The `GraphBuilder` class dynamically constructs the appropriate graph based on the selected use case (e.g., basic chatbot, sushi recommendation, agentic assistant).
- Nodes are added and connected via edges, with conditional logic for advanced routing.
- This modular design allows for easy extension: new nodes and workflows can be added with minimal changes to the overall architecture.

### Benefits
- **Modularity:** Each node encapsulates a single responsibility, making the system easy to maintain and extend.
- **Parallelism:** Certain workflows (like report generation) can run multiple nodes in parallel for efficiency.
- **Dynamic Routing:** The use of conditional edges enables intelligent decision-making and fallback strategies within the conversation flow.

---

## Example Use Case

1. **User:** "Find me a sushi restaurant near Marienplatz with good reviews and available parking."
2. **Agent:**
   - Searches for sushi restaurants near Marienplatz.
   - Retrieves menu, contact info, and Google reviews.
   - Checks parking availability and distance.
   - Presents a concise, actionable summary with all relevant details.

---

## Extensibility
- **Add New Tools:** Easily extendable by adding new MCP tool scripts for other domains (e.g., hotels, events).
- **Swap LLMs:** Supports multiple LLM backends for flexibility and experimentation.
- **Custom Data:** Can ingest new data sources by updating local JSON files or integrating new APIs.

---

## Conclusion

The Munich Sushi Chatbot demonstrates a robust, modular approach to building AI-powered assistants for location-based recommendations. Its architecture allows for easy expansion, real-time data integration, and a seamless user experience for anyone seeking sushi and parking in Munich. 