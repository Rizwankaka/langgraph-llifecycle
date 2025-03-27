"""
LangGraph workflow definition and compilation.
"""
import streamlit as st
from langgraph.graph import StateGraph, END
from workflow.state import WorkflowState
from workflow.nodes import (
    gather_requirements,
    create_user_stories,
    create_design,
    generate_code,
    security_review,
    write_test_cases,
    qa_testing,
    deployment,
    monitoring_and_feedback,
    maintenance_and_updates,
    product_owner_review,
    revise_user_stories,
    design_review,
    code_review,
    fix_code_after_code_review,
    fix_code_after_security,
    test_cases_review,
    fix_test_cases_after_review,
    fix_code_after_qa_feedback
)
from workflow.decisions import (
    decide_after_po_review,
    decide_after_design_review,
    decide_after_code_review,
    decide_after_security_review,
    decide_after_test_cases_review,
    decide_after_qa_testing
)

def create_workflow_graph():
    """Create and compile the LangGraph workflow."""
    # Create a state graph with our state type
    workflow = StateGraph(WorkflowState)
    
    # Add nodes for each step in the software development workflow
    workflow.add_node("gather_requirements", gather_requirements)
    workflow.add_node("create_user_stories", create_user_stories)
    workflow.add_node("product_owner_review", product_owner_review)
    workflow.add_node("revise_user_stories", revise_user_stories)
    workflow.add_node("create_design", create_design)
    workflow.add_node("design_review", design_review)
    workflow.add_node("generate_code", generate_code)
    workflow.add_node("code_review", code_review)
    workflow.add_node("fix_code_after_code_review", fix_code_after_code_review)
    workflow.add_node("security_review", security_review)
    workflow.add_node("fix_code_after_security", fix_code_after_security)
    workflow.add_node("write_test_cases", write_test_cases)
    workflow.add_node("test_cases_review", test_cases_review)
    workflow.add_node("fix_test_cases_after_review", fix_test_cases_after_review)
    workflow.add_node("qa_testing", qa_testing)
    workflow.add_node("fix_code_after_qa_feedback", fix_code_after_qa_feedback)
    workflow.add_node("deployment", deployment)
    workflow.add_node("monitoring_and_feedback", monitoring_and_feedback)
    workflow.add_node("maintenance_and_updates", maintenance_and_updates)
    
    # Define the workflow exactly as in ramadan.py
    workflow.set_entry_point("gather_requirements")
    
    workflow.add_edge("gather_requirements", "create_user_stories")
    workflow.add_edge("create_user_stories", "product_owner_review")
    
    workflow.add_conditional_edges(
        "product_owner_review", 
        decide_after_po_review, 
        {
            "create_design": "create_design", 
            "revise_user_stories": "revise_user_stories"
        }
    )
    workflow.add_edge("revise_user_stories", "product_owner_review")
    workflow.add_edge("create_design", "design_review")
    
    workflow.add_conditional_edges(
        "design_review", 
        decide_after_design_review, 
        {
            "generate_code": "generate_code", 
            "create_design": "create_design"
        }
    )
    workflow.add_edge("generate_code", "code_review")
    
    workflow.add_conditional_edges(
        "code_review", 
        decide_after_code_review, 
        {
            "security_review": "security_review", 
            "fix_code_after_code_review": "fix_code_after_code_review"
        }
    )
    workflow.add_edge("fix_code_after_code_review", "code_review")
    
    workflow.add_conditional_edges(
        "security_review", 
        decide_after_security_review, 
        {
            "write_test_cases": "write_test_cases", 
            "fix_code_after_security": "fix_code_after_security"
        }
    )
    workflow.add_edge("fix_code_after_security", "security_review")
    workflow.add_edge("write_test_cases", "test_cases_review")
    
    workflow.add_conditional_edges(
        "test_cases_review", 
        decide_after_test_cases_review, 
        {
            "qa_testing": "qa_testing", 
            "fix_test_cases_after_review": "fix_test_cases_after_review"
        }
    )
    workflow.add_edge("fix_test_cases_after_review", "test_cases_review")
    
    workflow.add_conditional_edges(
        "qa_testing", 
        decide_after_qa_testing, 
        {
            "deployment": "deployment", 
            "fix_code_after_qa_feedback": "fix_code_after_qa_feedback"
        }
    )
    workflow.add_edge("fix_code_after_qa_feedback", "qa_testing")
    workflow.add_edge("deployment", "monitoring_and_feedback")
    workflow.add_edge("monitoring_and_feedback", "maintenance_and_updates")
    workflow.add_edge("maintenance_and_updates", END)
    
    # Compile the workflow
    compiled_workflow = workflow.compile()
    
    return compiled_workflow