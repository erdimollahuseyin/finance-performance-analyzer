import streamlit as st
from app.nodes import (
    gather_financials_node,
    analyze_data_node,
    research_competitors_node,
    compare_performance_node,
    collect_feedback_node,
    research_critique_node,
    write_report_node,
    should_continue,
)
from app.utils import load_env_variables
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

# Load environment variables
load_env_variables()

# Initialize memory
memory = MemorySaver()

# Create the state graph
builder = StateGraph()
builder.add_node("gather_financials", gather_financials_node)
builder.add_node("analyze_data", analyze_data_node)
builder.add_node("research_competitors", research_competitors_node)
builder.add_node("compare_performance", compare_performance_node)
builder.add_node("collect_feedback", collect_feedback_node)
builder.add_node("research_critique", research_critique_node)
builder.add_node("write_report", write_report_node)
builder.set_entry_point("gather_financials")
builder.add_conditional_edges(
    "compare_performance", should_continue, {END: END, "collect_feedback": "collect_feedback"}
)
builder.add_edge("gather_financials", "analyze_data")
builder.add_edge("analyze_data", "research_competitors")
builder.add_edge("research_competitors", "compare_performance")
builder.add_edge("compare_performance", "collect_feedback")
builder.add_edge("collect_feedback", "research_critique")
builder.add_edge("research_critique", "compare_performance")
builder.add_edge("compare_performance", "write_report")
graph = builder.compile(checkpointer=memory)

# Streamlit UI
def main():
    st.title("Finansal Performans Raporlama Aracısı")
    task = st.text_input(
        "Görevi girin:", "Şirketinizin (Koç Holding A.Ş.) finansal performansını rakiplerle karşılaştırın"
    )
    competitors = st.text_area("Rakip isimlerini girin (her birini yeni satıra yazın):").split("\n")
    max_revisions = st.number_input("Maksimum Revizyonlar", min_value=1, value=2)
    uploaded_file = st.file_uploader("Şirketin finansal verilerini içeren CSV dosyasını yükleyin", type=["csv"])

    if st.button("Analiz Başlat") and uploaded_file is not None:
        csv_data = uploaded_file.getvalue().decode("utf-8")
        initial_state = {
            "task": task,
            "competitors": [comp.strip() for comp in competitors],
            "csv_file": csv_data,
            "max_revisions": max_revisions,
            "revision_number": 1,
        }
        thread = {"configurable": {"thread_id": "1"}}
        final_state = None
        for s in graph.stream(initial_state, thread):
            st.write(s)
            final_state = s
        if final_state and "report" in final_state:
            st.subheader("Final Rapor")
            st.write(final_state["report"])

if __name__ == "__main__":
    main()
