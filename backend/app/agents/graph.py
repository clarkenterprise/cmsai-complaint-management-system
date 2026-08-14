from langgraph.graph import END, START, StateGraph

from app.agents.nodes import (
    assess_risk,
    extract_complaint,
    check_completeness,
    generate_capa,
)
from app.agents.state import ComplaintState


def build_complaint_graph():
    graph = StateGraph(ComplaintState)

    graph.add_node("extract_complaint", extract_complaint)
    graph.add_node("assess_risk", assess_risk)
    graph.add_node("check_completeness", check_completeness)
    graph.add_node(
    "generate_capa",
    generate_capa
)

    graph.add_edge(START, "extract_complaint")
    graph.add_edge("extract_complaint", "assess_risk")
    graph.add_edge("assess_risk", "check_completeness")
    graph.add_edge("check_completeness", "generate_capa")
    graph.add_edge("generate_capa", END)

    return graph.compile()


complaint_graph = build_complaint_graph()