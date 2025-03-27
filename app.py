"""
LangGraph-powered DevOps Workflow Simulator - Main Application
"""
import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
print("Attempted to load environment variables from .env file.") # For debugging

# Import modules
from components.sidebar import setup_sidebar
from components.progress import render_progress_tracker
from workflow.graph import create_workflow_graph
from utils.visualization import generate_workflow_graph, display_workflow_graph
from config.settings import APP_TITLE, APP_DESCRIPTION

def main():
    # Page configuration
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🔄",
        layout="wide"
    )
    
    # Display header
    st.title("🔄 " + APP_TITLE)
    st.markdown(APP_DESCRIPTION)
    
    # Setup sidebar and get selected provider
    selected_llm_provider = setup_sidebar()
    
    # User requirements input
    st.header("Project Requirements")
    default_requirements = "User wants a login page with username/password fields. Include a 'Forgot Password' link. Also, support Single Sign-On (SSO) via Google."

    if 'user_requirements_input' not in st.session_state:
        st.session_state.user_requirements_input = default_requirements

    user_requirements = st.text_area(
        "Enter your project requirements here:",
        value=st.session_state.user_requirements_input,
        height=150,
        help="Describe what you want to build. Be as specific as possible to get better results."
    )

    # Store the requirements in session state when changed
    if user_requirements != st.session_state.user_requirements_input:
        st.session_state.user_requirements_input = user_requirements
    
    # Display progress tracker
    st.header("Progress")
    render_progress_tracker()
    
    # Get the workflow graph
    workflow_graph = create_workflow_graph()
    
    # Visualize the workflow graph
    with st.expander("Show Workflow Graph", expanded=True):
        graph_image = generate_workflow_graph(workflow_graph)
        display_workflow_graph(graph_image)
    
    # Create Start Workflow button
    start_workflow_col1, start_workflow_col2 = st.columns([1, 3])
    
    with start_workflow_col1:
        start_workflow = st.button("Start Workflow", type="primary", use_container_width=True)

    with start_workflow_col2:
        if 'workflow_running' in st.session_state and st.session_state.workflow_running:
            st.info("Workflow is running... See status in the log section below.")
    
    # Reset session state if needed
    if 'workflow_reset' not in st.session_state:
        st.session_state.workflow_reset = False

    if 'workflow_result' not in st.session_state:
        st.session_state.workflow_result = None

    if 'workflow_running' not in st.session_state:
        st.session_state.workflow_running = False
    
    # Execute the workflow when button is clicked
    if start_workflow or ('workflow_running' in st.session_state and st.session_state.workflow_running):
        try:
            st.session_state.workflow_running = True
            
            # Clear previously completed steps and reset progress tracking
            if 'completed_steps' in st.session_state:
                st.session_state.completed_steps = set()
            if 'highest_step' in st.session_state:
                st.session_state.highest_step = -1
                
            # Create initial state with all fields needed by the workflow
            initial_state = {
                "user_requirements": user_requirements,
                "user_stories": None,
                "po_review_outcome": None,
                "po_review_feedback": None,
                "design_documents": None,
                "design_review_outcome": None,
                "design_review_feedback": None,
                "generated_code": None,
                "code_review_outcome": None,
                "code_review_feedback": None,
                "security_review_outcome": None,
                "security_review_feedback": None,
                "test_cases": None,
                "test_case_review_outcome": None,
                "test_case_review_feedback": None,
                "qa_test_outcome": None,
                "qa_test_feedback": None,
                "deployment_status": None,
                "monitoring_feedback": None,
                "maintenance_updates_log": [],
                "llm_provider": selected_llm_provider,
                "step_counter": 0
            }
            
            # Display a spinner during execution
            with st.spinner("Running workflow... Please wait"):
                # Run the workflow
                st.session_state.workflow_result = workflow_graph.invoke(initial_state)
            
            # Display completion message
            st.balloons()
            st.success("✅ Workflow completed successfully!")
            
            # Add workflow completion summary
            if st.session_state.workflow_result:
                with st.expander("Workflow Completion Summary", expanded=True):
                    # Create a summary table of all completed steps
                    summary_data = []
                    if 'completed_steps' in st.session_state:
                        for step in sorted(st.session_state.completed_steps):
                            summary_data.append({"Step": step.capitalize(), "Status": "✅ Completed"})
                    
                    if summary_data:
                        st.write("### Workflow Steps Completed")
                        # Display steps in a table format
                        for item in summary_data:
                            st.write(f"**{item['Step']}**: {item['Status']}")
                        
                    # Show final code if available
                    if st.session_state.workflow_result.get("generated_code"):
                        st.write("### Final Generated Code")
                        st.code(st.session_state.workflow_result.get("generated_code"), language="python")
                
        except Exception as e:
            st.error(f"Error executing workflow: {e}")
            import traceback
            st.error(traceback.format_exc())

if __name__ == "__main__":
    main()