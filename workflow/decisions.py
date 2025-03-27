"""
Decision functions for LangGraph workflow.
"""
import streamlit as st

def decide_after_po_review(state):
    """Determine whether to proceed to design creation or revise user stories after PO review."""
    st.info("--- Decision: After PO Review ---")
    
    # Check step counter to prevent infinite loops
    step_counter = state.get("step_counter", 0)
    if step_counter > 25:  # Safety limit
        st.warning("Maximum steps reached. Forcing progress to next stage.")
        return "create_design"
    
    outcome = state.get("po_review_outcome")
    if outcome == "Approved": 
        st.info("   Routing to: Create Design Documents")
        return "create_design"
    else: 
        st.info("   Routing to: Revise User Stories")
        return "revise_user_stories"

def decide_after_design_review(state):
    """Determine whether to proceed to code generation or revise design after design review."""
    st.info("--- Decision: After Design Review ---")
    
    # Check step counter to prevent infinite loops
    step_counter = state.get("step_counter", 0)
    if step_counter > 25:  # Safety limit
        st.warning("Maximum steps reached. Forcing progress to next stage.")
        return "generate_code"
    
    outcome = state.get("design_review_outcome")
    if outcome == "Approved": 
        st.info("   Routing to: Generate Code")
        return "generate_code"
    else: 
        st.info("   Routing to: Create Design Documents (Feedback received)")
        return "create_design"

def decide_after_code_review(state):
    """Determine whether to proceed to security review or fix code after code review."""
    st.info("--- Decision: After Code Review ---")
    
    # Check step counter to prevent infinite loops
    step_counter = state.get("step_counter", 0)
    if step_counter > 25:  # Safety limit
        st.warning("Maximum steps reached. Forcing progress to next stage.")
        return "security_review"
    
    outcome = state.get("code_review_outcome")
    if outcome == "Approved":
        st.info("   Routing to: Security Review")
        return "security_review"
    else:
        st.info("   Routing to: Fix Code after Code Review")
        return "fix_code_after_code_review"

def decide_after_security_review(state):
    """Determine whether to proceed to test cases or fix code after security review."""
    st.info("--- Decision: After Security Review ---")
    
    # Check step counter to prevent infinite loops
    step_counter = state.get("step_counter", 0)
    if step_counter > 25:  # Safety limit
        st.warning("Maximum steps reached. Forcing progress to next stage.")
        return "write_test_cases"
    
    outcome = state.get("security_review_outcome")
    if outcome == "Approved": 
        st.info("   Routing to: Write Test Cases") 
        return "write_test_cases"
    else: 
        st.info("   Routing to: Fix Code after Security")
        return "fix_code_after_security"

def decide_after_test_cases_review(state):
    """Determine whether to proceed to QA testing or fix test cases after review."""
    st.info("--- Decision: After Test Cases Review ---")
    
    # Check step counter to prevent infinite loops
    step_counter = state.get("step_counter", 0)
    if step_counter > 25:  # Safety limit
        st.warning("Maximum steps reached. Forcing progress to next stage.")
        return "qa_testing"
    
    outcome = state.get("test_case_review_outcome")
    if outcome == "Approved": 
        st.info("   Routing to: QA Testing") 
        return "qa_testing"
    else: 
        st.info("   Routing to: Fix Test Cases after Review")
        return "fix_test_cases_after_review"

def decide_after_qa_testing(state):
    """Determine whether to proceed to deployment or fix code after QA testing."""
    st.info("--- Decision: After QA Testing ---")
    
    # Check step counter to prevent infinite loops
    step_counter = state.get("step_counter", 0)
    if step_counter > 25:  # Safety limit
        st.warning("Maximum steps reached. Forcing progress to next stage.")
        return "deployment"
    
    outcome = state.get("qa_test_outcome")
    if outcome == "Passed": 
        st.info("   Routing to: Deployment")
        return "deployment"
    else:
        st.info("   Routing to: Fix Code after QA Feedback")
        return "fix_code_after_qa_feedback"