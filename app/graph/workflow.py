"""Workflow Graph Assembly and Compilation.

Constructs the cyclic LangGraph multi-agent orchestration graph:
    [START]
       │
       ▼
   [planner]
       │
       ▼
 ┌──>[coder]
 │     │
 │     ▼
 │ [executor]
 │     │
 │     ├─(exit_code == 0)───────────────────────> [END] (Success)
 │     ├─(iterations >= max)───────────────────> [END] (Circuit Breaker Tripped)
 │     │
 └──[reviewer] ◄─(exit_code != 0 & iter < max)──┘
"""

from langgraph.graph import StateGraph, START, END
from app.graph.state import AgentState
from app.graph.nodes.planner import planner_node
from app.graph.nodes.coder import coder_node
from app.graph.nodes.executor import executor_node
from app.graph.nodes.reviewer import reviewer_node
from app.graph.edges import route_after_execution


def create_code_workspace_graph():
    """Builds and compiles the cyclic agent StateGraph."""
    # Initialize the graph with the typed state schema
    workflow = StateGraph(AgentState)

    # 1. Register Core Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("reviewer", reviewer_node)

    # 2. Add Deterministic Transitions
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "coder")
    workflow.add_edge("coder", "executor")

    # 3. Add Conditional Routing Edge from Executor
    # Routes to END on success or limit reached, or to reviewer on failure
    workflow.add_conditional_edges(
        "executor",
        route_after_execution,
        {
            "success": END,
            "reviewer": "reviewer",
            "max_iterations_reached": END,
        },
    )

    # 4. Add Cyclic Edge: Reviewer routes back to Coder with debugging feedback
    workflow.add_edge("reviewer", "coder")

    # 5. Compile the graph into a runnable application
    return workflow.compile()


# Compiled singleton graph instance
app_graph = create_code_workspace_graph()

