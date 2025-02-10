from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from nodes import (
    AgentState,
    analyze_data_node,
    collect_feedback_node,
    compare_performance_node,
    gather_financials_node,
    research_competitors_node,
    research_critique_node,
    should_continue,
    write_report_node,
)


def create_state_graph():
    memory = MemorySaver()
    builder = StateGraph(AgentState)

    # Define nodes and edges
    nodes = {
        "gather_financials": gather_financials_node,
        "analyze_data": analyze_data_node,
        "research_competitors": research_competitors_node,
        "compare_performance": compare_performance_node,
        "collect_feedback": collect_feedback_node,
        "research_critique": research_critique_node,
        "write_report": write_report_node,
    }

    edges = [
        ("gather_financials", "analyze_data"),
        ("analyze_data", "research_competitors"),
        ("research_competitors", "compare_performance"),
        ("compare_performance", "collect_feedback"),
        ("collect_feedback", "research_critique"),
        ("research_critique", "compare_performance"),
        ("compare_performance", "write_report"),
    ]

    # Add nodes to the state graph
    for node_name, node_func in nodes.items():
        builder.add_node(node_name, node_func)

    # Set entry point
    builder.set_entry_point("gather_financials")

    # Add edges to the state graph
    for from_node, to_node in edges:
        builder.add_edge(from_node, to_node)

    # Add conditional edges
    builder.add_conditional_edges(
        "compare_performance", should_continue, {END: END, "collect_feedback": "collect_feedback"}
    )

    # Compile the graph with memory checkpointer
    return builder.compile(checkpointer=memory)


# Create the state graph
graph = create_state_graph()
