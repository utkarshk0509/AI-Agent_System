"""Builds the LangGraph workflow.

    START -> planner -> coder -> executor
                          ^         |
                          |         |-- worked and printed output --> answer -> END
                          |         |-- hit max_iterations ---------> END
                          |         |
                          +--- reviewer <-- failed
"""

from langgraph.graph import END, START, StateGraph

from app.graph.edges import route_after_execution
from app.graph.nodes.answer import answer_node
from app.graph.nodes.coder import coder_node
from app.graph.nodes.executor import executor_node
from app.graph.nodes.planner import planner_node
from app.graph.nodes.reviewer import reviewer_node
from app.graph.state import AgentState


def create_code_workspace_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("answer", answer_node)

    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "coder")
    workflow.add_edge("coder", "executor")
    workflow.add_conditional_edges(
        "executor",
        route_after_execution,
        {
            "success": "answer",
            "reviewer": "reviewer",
            "max_iterations_reached": END,
        },
    )
    workflow.add_edge("reviewer", "coder")
    workflow.add_edge("answer", END)

    return workflow.compile()


app_graph = create_code_workspace_graph()
