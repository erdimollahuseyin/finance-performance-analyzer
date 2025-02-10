import pandas as pd
from io import StringIO

from config import LLM_NAME, OPENAI_API_KEY, TAVILY_API_KEY
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END
from models import AgentState, Queries
from prompts import (
    ANALYZE_DATA_PROMPT,
    COMPETE_PERFORMANCE_PROMPT,
    FEEDBACK_PROMPT,
    GATHER_FINANCIALS_PROMPT,
    RESEARCH_COMPETITORS_PROMPT,
    RESEARCH_CRITIQUE_PROMPT,
    WRITE_REPORT_PROMPT,
)
from tavily import TavilyClient

# Initialize models and clients
model = ChatOpenAI(api_key=OPENAI_API_KEY, model=LLM_NAME)
tavily = TavilyClient(api_key=TAVILY_API_KEY)


def gather_financials_node(state: AgentState):
    """
    Gathers financial data from a CSV file and prepares it for analysis.

    Args:
        state (AgentState): The state object containing the task description and CSV file content.

    Returns:
        dict: A dictionary containing the financial data response from the model.
    """
    df = pd.read_csv(StringIO(state["csv_file"]))
    financial_data_str = df.to_string(index=False)
    combined_content = f"{state['task']}\n\nHere are the financial data:\n\n{financial_data_str}"
    messages = [
        SystemMessage(content=GATHER_FINANCIALS_PROMPT),
        HumanMessage(content=combined_content),
    ]
    response = model.invoke(messages)
    return {"financial_data": response.content}


def analyze_data_node(state: AgentState):
    """
    Analyzes financial data using a model and returns the analysis.

    Args:
        state (AgentState): The state containing financial data to be analyzed.

    Returns:
        dict: A dictionary containing the analysis result with the key 'analysis'.
    """
    messages = [
        SystemMessage(content=ANALYZE_DATA_PROMPT),
        HumanMessage(content=state["financial_data"]),
    ]
    response = model.invoke(messages)
    return {"analysis": response.content}


def research_competitors_node(state: AgentState):
    """
    Research competitors and gather relevant content.

    This function takes an AgentState object, retrieves the list of competitors,
    and performs a search for each competitor using a predefined prompt. The search
    results are then aggregated and returned as a dictionary containing the content.

    Args:
        state (AgentState): The state object containing the current state information,
                            including the list of competitors and existing content.

    Returns:
        dict: A dictionary with a single key "content" containing the aggregated search results.
    """
    content = state.get("content", [])
    for competitor in state["competitors"]:
        queries = model.with_structured_output(Queries).invoke(
            [
                SystemMessage(content=RESEARCH_COMPETITORS_PROMPT),
                HumanMessage(content=competitor),
            ]
        )
        for q in queries.queries:
            response = tavily.search(query=q, max_results=2)
            content.extend(r["content"] for r in response["results"])
    return {"content": content}


def compare_performance_node(state: AgentState):
    """
    Compares the performance based on the given state and generates a response.

    Args:
        state (AgentState): The state containing the task, analysis, and other relevant information.

    Returns:
        dict: A dictionary containing the comparison result and the updated revision number.
    """
    content = "\n\n".join(state.get("content", []))
    user_message = HumanMessage(
        content=f"{state['task']}\n\nHere is the financial analysis:\n\n{state['analysis']}"
    )
    messages = [
        SystemMessage(content=COMPETE_PERFORMANCE_PROMPT.format(content=content)),
        user_message,
    ]
    response = model.invoke(messages)
    return {
        "comparison": response.content,
        "revision_number": state.get("revision_number", 1) + 1,
    }


def research_critique_node(state: AgentState):
    """
    Processes the feedback from the state using a model to generate queries,
    performs a search for each query, and aggregates the content from the search results.

    Args:
        state (AgentState): The state containing feedback and optionally existing content.

    Returns:
        dict: A dictionary with the key "content" containing the aggregated content from the search results.
    """
    queries = model.with_structured_output(Queries).invoke(
        [
            SystemMessage(content=RESEARCH_CRITIQUE_PROMPT),
            HumanMessage(content=state["feedback"]),
        ]
    )
    content = state.get("content", [])
    for q in queries.queries:
        response = tavily.search(query=q, max_results=2)
        content.extend(r["content"] for r in response["results"])
    return {"content": content}


def collect_feedback_node(state: AgentState):
    """
    Collects feedback from the model based on the given agent state.

    Args:
        state (AgentState): The current state of the agent, which includes a comparison message.

    Returns:
        dict: A dictionary containing the feedback response from the model.
    """
    messages = [
        SystemMessage(content=FEEDBACK_PROMPT),
        HumanMessage(content=state["comparison"]),
    ]
    response = model.invoke(messages)
    return {"feedback": response.content}


def write_report_node(state: AgentState):
    """
    Generates a report based on the given agent state.

    Args:
        state (AgentState): The current state of the agent, which includes a comparison key.

    Returns:
        dict: A dictionary containing the generated report with the key "report".
    """
    messages = [
        SystemMessage(content=WRITE_REPORT_PROMPT),
        HumanMessage(content=state["comparison"]),
    ]
    response = model.invoke(messages)
    return {"report": response.content}


def should_continue(state: AgentState):
    """
    Determines whether the agent should continue its operation or end it based on the revision number.

    Args:
        state (AgentState): The current state of the agent, which includes the revision number and the maximum allowed revisions.

    Returns:
        str: Returns "END" if the current revision number exceeds the maximum allowed revisions, otherwise returns "collect_feedback".
    """
    return END if state["revision_number"] > state["max_revisions"] else "collect_feedback"
