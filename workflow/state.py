"""
State definitions for the LangGraph workflow.
"""
from typing import TypedDict, Annotated, List, Optional
import operator

class WorkflowState(TypedDict):
    """Represents the data passed between steps in the workflow."""
    # Requirements and User Stories
    user_requirements: Optional[str]
    user_stories: Optional[str]
    
    # PO Review
    po_review_outcome: Optional[str]
    po_review_feedback: Optional[str]
    
    # Design
    design_documents: Optional[str]
    design_review_outcome: Optional[str]
    design_review_feedback: Optional[str]
    
    # Code Generation and Review
    generated_code: Optional[str]
    code_review_outcome: Optional[str]
    code_review_feedback: Optional[str]
    
    # Security Review
    security_review_outcome: Optional[str]
    security_review_feedback: Optional[str]
    
    # Testing
    test_cases: Optional[str]
    test_case_review_outcome: Optional[str]
    test_case_review_feedback: Optional[str]
    
    # QA
    qa_test_outcome: Optional[str]
    qa_test_feedback: Optional[str]
    
    # Deployment and Monitoring
    deployment_status: Optional[str]
    monitoring_feedback: Optional[str]
    maintenance_updates_log: Annotated[list[str], operator.add]
    
    # Configuration
    llm_provider: Optional[str]
    
    # Workflow Control
    step_counter: int  # Counter to prevent infinite recursion