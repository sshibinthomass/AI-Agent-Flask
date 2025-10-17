import os
from dotenv import load_dotenv
load_dotenv()
from typing import Annotated, List
import operator
from typing_extensions import Literal
from pydantic import BaseModel,Field
from langchain_core.messages import HumanMessage,SystemMessage
from typing_extensions import TypedDict
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.constants import Send
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from datetime import datetime
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

os.environ["OPENAI_API_KEY"]=os.getenv("OPENAI_API_KEY")
os.environ["GROQ_API_KEY"]=os.getenv("GROQ_API_KEY")
os.environ["TAVILY_API_KEY"]=os.getenv("TAVILY_API_KEY")
os.environ["GEMINI_API_KEY"]=os.getenv("GEMINI_API_KEY")

#llm=ChatOpenAI(model="gpt-4.1-mini")
#llm=ChatGroq(model="llama-3.3-70b-versatile")
llm=ChatGroq(model="qwen-qwq-32b")

# Schema for structured output to use in planning
class Section(BaseModel):
    name:str=Field(description="Name for this section of the report")
    description:str=Field(description="Brief Overview of the main topics and concepts of the section")

class Sections(BaseModel):
    sections:List[Section]=Field(
        description="Sections of the report"
    )

# Augment the LLM with schema for structured output


# Graph state
class State(TypedDict):
    topic: str  # Report topic
    sections: list[Section]  # List of report sections
    completed_sections: Annotated[
        list, operator.add
    ]  # All workers write to this key in parallel
    final_report: str  # Final report
    markdown_file: str  # Path to exported markdown file

# Worker state
class WorkerState(TypedDict):
    section: Section
    completed_sections: Annotated[list, operator.add]


# Nodes
async def orchestrator(state: State):
    """Orchestrator that generates a plan for the report"""
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
    
    # Bind tools to LLM and then add structured output
    llm_with_tools = llm.bind_tools(tools)
    planner = llm_with_tools.with_structured_output(Sections)

    # Generate queries
    report_sections = planner.invoke(
        [
            SystemMessage(content="Generate a clear and organized list of five topics and descriptions of words 20 to 30 to include in a restaurant report. The report should cover the restaurant’s name and description, location, menu, parking options, contact details, Google reviews, nearby restaurants, and any other relevant information. Use available tools or knowledge if needed to suggest comprehensive and logical report sections."),
            HumanMessage(content=f"Here is the report topic: {state['topic']}"),
        ]
    )

    print("Report Sections:",report_sections)

    return {"sections": report_sections.sections}

async def llm_call(state: WorkerState):
    """Worker writes a section of the report"""
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
    agent=create_react_agent(
        llm, tools
    )
    # Generate section
    result = await agent.ainvoke({
        "messages": [
            SystemMessage(
                content="Using the provided topic and description, write a complete and well-structured section of words 100 to 150 for a restaurant report. Include relevant details and also the tools if needed. Use markdown formatting."
            ),
            HumanMessage(
                content=f"Here is the section name: {state['section'].name} and description: {state['section'].description}"
            )
        ]
    })
    
    # Extract the final message content from the agent response
    if isinstance(result, dict) and 'messages' in result:
        final_message = result['messages'][-1]
        section_content = final_message.content
    elif hasattr(result, 'messages'):
        final_message = result.messages[-1]
        section_content = final_message.content
    else:
        # Fallback: try to get content directly
        section_content = str(result)
    
    print("Section:", section_content)
    
    # Return the correct dictionary format expected by LangGraph
    return {"completed_sections": [section_content]}

# Conditional edge function to create llm_call workers that each write a section of the report
def assign_workers(state: State):
    """Assign a worker to each section in the plan"""

    # Kick off section writing in parallel via Send() API
    return [Send("llm_call", {"section": s}) for s in state["sections"]]

def synthesizer(state: State):
    """Synthesize full report from sections"""

    # List of completed sections
    completed_sections = state["completed_sections"]

    # Format completed section to str to use as context for final sections
    completed_report_sections = "\n\n---\n\n".join(completed_sections)

    return {"final_report": completed_report_sections}

def export_markdown(state: State):
    """Export the final report to a markdown file"""
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{timestamp}.md"
    
    # Create the full markdown content with title
    markdown_content = f"# {state['topic']}\n\n"
    markdown_content += f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    markdown_content += "---\n\n"
    markdown_content += state['final_report']
    
    # Ensure the reports directory exists
    os.makedirs("reports", exist_ok=True)
    
    # Write to file
    filepath = os.path.join("reports", filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"Report exported to: {filepath}")
    
    return {"markdown_file": filepath}


# Build workflow


orchestrator_worker_builder = StateGraph(State)

# Add the nodes
orchestrator_worker_builder.add_node("orchestrator", orchestrator)
orchestrator_worker_builder.add_node("llm_call", llm_call)
orchestrator_worker_builder.add_node("synthesizer", synthesizer)
orchestrator_worker_builder.add_node("export_markdown", export_markdown)

# Add edges to connect nodes
orchestrator_worker_builder.add_edge(START, "orchestrator")
orchestrator_worker_builder.add_conditional_edges(
    "orchestrator", assign_workers, ["llm_call"]
)
orchestrator_worker_builder.add_edge("llm_call", "synthesizer")
orchestrator_worker_builder.add_edge("synthesizer", "export_markdown")
orchestrator_worker_builder.add_edge("export_markdown", END)

# Compile the workflow
orchestrator_worker = orchestrator_worker_builder.compile()

async def main():
    state = await orchestrator_worker.ainvoke({"topic": "Create a report about the restaurant Sasou in Munich"})
    print(f"\nReport saved to: {state['markdown_file']}")

# Run the async function
if __name__ == "__main__":
    asyncio.run(main())