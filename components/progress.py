"""
Progress tracking UI components.
"""
import streamlit as st

# Define all workflow steps in order
WORKFLOW_STEPS = [
    "requirements",
    "user_stories", 
    "user_stories_review",
    "design", 
    "design_review",
    "code", 
    "code_review",
    "security", 
    "testing", 
    "test_review",
    "qa", 
    "deployment", 
    "monitoring"
]

def mark_step_complete(step):
    """Mark a step as complete in session state."""
    if 'completed_steps' not in st.session_state:
        st.session_state.completed_steps = set()
    st.session_state.completed_steps.add(step)
    
    # Update the highest step completed for visual tracking
    if 'highest_step' not in st.session_state:
        st.session_state.highest_step = -1
    
    current_step_index = WORKFLOW_STEPS.index(step) if step in WORKFLOW_STEPS else -1
    if current_step_index > st.session_state.highest_step:
        st.session_state.highest_step = current_step_index

def render_progress_tracker():
    """Show progress tracker on the UI."""
    if 'completed_steps' not in st.session_state:
        st.session_state.completed_steps = set()
        
    # Calculate progress percentage based on completed steps
    total_steps = len(WORKFLOW_STEPS)
    completed_count = sum(1 for step in WORKFLOW_STEPS if step in st.session_state.completed_steps)
    progress_percentage = completed_count / total_steps if total_steps > 0 else 0
    
    # Use a horizontal progress bar for overall completion
    st.progress(progress_percentage, text=f"Overall Progress: {int(progress_percentage * 100)}%")
    
    # Create columns for step display
    cols = st.columns(len(WORKFLOW_STEPS))
    
    # Display step indicators
    for i, step_id in enumerate(WORKFLOW_STEPS):
        step_name = step_id.replace('_', ' ').title()
        with cols[i]:
            if step_id in st.session_state.completed_steps:
                st.success(f"✅")
                st.caption(f"{step_name}")
            elif 'highest_step' in st.session_state and i == st.session_state.highest_step + 1:
                st.info(f"⏳")  # Next step
                st.caption(f"{step_name}")
            else:
                st.write(f"○")  # Future step
                st.caption(f"{step_name}")

    # Add a small spacing after the progress tracker
    st.write("")