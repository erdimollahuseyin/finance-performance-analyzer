import pandas as pd
from io import StringIO
from app.prompts import (
    GATHER_FINANCIALS_PROMPT,
    ANALYZE_DATA_PROMPT,
    RESEARCH_COMPETITORS_PROMPT,
    COMPETE_PERFORMANCE_PROMPT,
    FEEDBACK_PROMPT,
    WRITE_REPORT_PROMPT,
    RESEARCH_CRITIQUE_PROMPT,
)
from app.utils import model, tavily
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from typing import List, TypedDict
from langgraph.graph import END


class AgentState(TypedDict):
    task: str
    competitors: List[str]
    csv_file: str
    financial_data: str
    analysis: str
    comparison: str
    feedback: str
    report: str
    content: List[str]
    revision_number: int
    max_revisions: int

class Queries(BaseModel):
    queries: List[str]


def gather_financials_node(state: AgentState):
    df = pd.read_csv(StringIO(state["csv_file"]))
    financial_data_str = df.to_string(index=False)
    combined_content = f"{state['task']}\n\nİşte finansal veriler:\n\n{financial_data_str}"
    messages = [SystemMessage(content=GATHER_FINANCIALS_PROMPT), HumanMessage(content=combined_content)]
    response = model.invoke(messages)
    return {"financial_data": response.content}


def analyze_data_node(state: AgentState):
    messages = [SystemMessage(content=ANALYZE_DATA_PROMPT), HumanMessage(content=state["financial_data"])]
    response = model.invoke(messages)
    return {"analysis": response.content}


def research_competitors_node(state: AgentState):
    content = state.get("content", [])
    for competitor in state["competitors"]:
        queries = model.with_structured_output(Queries).invoke(
            [SystemMessage(content=RESEARCH_COMPETITORS_PROMPT), HumanMessage(content=competitor)]
        )
        for q in queries.queries:
            response = tavily.search(query=q, max_results=2)
            for r in response["results"]:
                content.append(r["content"])
    return {"content": content}


def compare_performance_node(state: AgentState):
    content = "\n\n".join(state.get("content", []))
    user_message = HumanMessage(content=f"{state['task']}\n\nİşte finansal analiz:\n\n{state['analysis']}")
    messages = [SystemMessage(content=COMPETE_PERFORMANCE_PROMPT.format(content=content)), user_message]
    response = model.invoke(messages)
    return {"comparison": response.content, "revision_number": state.get("revision_number", 1) + 1}


def research_critique_node(state: AgentState):
    queries = model.with_structured_output(Queries).invoke(
        [SystemMessage(content=RESEARCH_CRITIQUE_PROMPT), HumanMessage(content=state["feedback"])]
    )
    content = state.get("content", [])
    for q in queries.queries:
        response = tavily.search(query=q, max_results=2)
        for r in response["results"]:
            content.append(r["content"])
    return {"content": content}


def collect_feedback_node(state: AgentState):
    messages = [SystemMessage(content=FEEDBACK_PROMPT), HumanMessage(content=state["comparison"])]
    response = model.invoke(messages)
    return {"feedback": response.content}


def write_report_node(state: AgentState):
    messages = [SystemMessage(content=WRITE_REPORT_PROMPT), HumanMessage(content=state["comparison"])]
    response = model.invoke(messages)
    return {"report": response.content}


def should_continue(state):
    return END if state["revision_number"] > state["max_revisions"] else "collect_feedback"