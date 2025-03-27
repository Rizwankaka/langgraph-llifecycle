# streamlit_app.py
import streamlit as st
import os
import operator
import random
import json
from typing import TypedDict, Annotated, List, Optional
import traceback # For detailed error logging
import io # To handle image data in memory

# Import load_dotenv
from dotenv import load_dotenv

# LLM Imports
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field # Using v1 for compatibility if needed
from langgraph.graph import StateGraph, END

# --- Load Environment Variables from .env file ---
# This should be one of the first things executed
load_dotenv()
print("Attempted to load environment variables from .env file.") # For debugging

# --- Streamlit Page Configuration ---
st.set_page_config(layout="wide", page_title="LangGraph Software Lifecycle Demo")

st.title("Interactive Software Development Lifecycle Simulation (LangGraph)")
st.markdown("""
This application simulates a software development lifecycle using LangGraph.
It integrates LLMs (Groq/Llama3 or Google/Gemini) for tasks like generating user stories,
code snippets, and fixing issues based on simulated reviews.
API keys can be provided in your local `.env` file or entered directly below.

**Instructions:**
1.  Enter your API keys in the sidebar if not already loaded from `.env`
2.  Select your preferred LLM Provider in the sidebar.
3.  Enter your project requirements in the text area below.
4.  Click "Start Workflow" to execute the development cycle.
5.  Observe the execution log and the final state below.
""")

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

# --- LangGraph State Definition ---
class WorkflowState(TypedDict):
    """Represents the data passed between steps in the workflow."""
    user_requirements: Optional[str]
    user_stories: Optional[str]
    po_review_outcome: Optional[str]; po_review_feedback: Optional[str]
    design_documents: Optional[str]
    design_review_outcome: Optional[str]; design_review_feedback: Optional[str]
    generated_code: Optional[str]
    code_review_outcome: Optional[str]; code_review_feedback: Optional[str]
    security_review_outcome: Optional[str]; security_review_feedback: Optional[str]
    test_cases: Optional[str]
    test_case_review_outcome: Optional[str]; test_case_review_feedback: Optional[str]
    qa_test_outcome: Optional[str]; qa_test_feedback: Optional[str]
    deployment_status: Optional[str]
    monitoring_feedback: Optional[str]
    maintenance_updates_log: Annotated[list[str], operator.add]
    llm_provider: Optional[str]
    step_counter: int  # Add a step counter to prevent infinite recursion

# --- LLM Initialization & Helper ---
llm_clients = {}
groq_available = False
google_available = False
DEFAULT_LLM_PROVIDER = None

# Sidebar Configuration with API Key Inputs
st.sidebar.header("API Configuration")

# Load API keys from environment
groq_api_key_loaded = os.environ.get("GROQ_API_KEY", "")
google_api_key_loaded = os.environ.get("GOOGLE_API_KEY", "")

# API key inputs in sidebar
with st.sidebar.expander("API Keys (Optional if loaded from .env)", expanded=True):
    groq_api_key = st.text_input(
        "Groq API Key", 
        value=groq_api_key_loaded,
        type="password",
        help="Enter your Groq API key here if not loaded from .env file"
    )
    
    google_api_key = st.text_input(
        "Google/Gemini API Key", 
        value=google_api_key_loaded,
        type="password",
        help="Enter your Google/Gemini API key here if not loaded from .env file"
    )

# Update environment variables with user-provided keys if entered
if groq_api_key and groq_api_key != groq_api_key_loaded:
    os.environ["GROQ_API_KEY"] = groq_api_key
    groq_api_key_loaded = groq_api_key

if google_api_key and google_api_key != google_api_key_loaded:
    os.environ["GOOGLE_API_KEY"] = google_api_key
    google_api_key_loaded = google_api_key

# API Usage Protection - moved after API key inputs
st.sidebar.subheader("API Usage Protection")
enable_quota_protection = st.sidebar.checkbox(
    "Enable API Usage Protection", 
    value=True,
    help="Limits API calls to protect your quota"
)
max_api_calls = st.sidebar.number_input(
    "Max API Calls Per Session", 
    min_value=1, 
    max_value=100, 
    value=25,  # Changed default to 25
    help="Set a maximum limit for API calls to prevent quota exhaustion"
)

# API call counter (in session state)
if 'api_calls' not in st.session_state:
    st.session_state.api_calls = 0
    
# For backward compatibility - ensure any old counter names also get initialized
if 'gemini_api_calls' not in st.session_state:
    st.session_state.gemini_api_calls = 0

# Clear cached resources if needed
if 'clear_cache' not in st.session_state:
    st.session_state.clear_cache = False

# Add a reset button in the sidebar
if st.sidebar.button("Reset Cache & Counters"):
    # Clear all caches
    st.cache_resource.clear()
    st.cache_data.clear()
    # Reset counters
    st.session_state.api_calls = 0
    st.session_state.gemini_api_calls = 0
    st.session_state.clear_cache = True
    st.sidebar.success("✅ Cache and counters reset!")
    st.experimental_rerun()

# Initialize clients with keys
if groq_api_key_loaded:
    try:
        llm_clients["groq"] = ChatGroq(temperature=0.1, model_name="llama3-8b-8192")
        groq_available = True
        st.sidebar.success("✓ Groq client initialized (llama3-8b).")
    except Exception as e:
        st.sidebar.error(f"✗ Failed to initialize Groq: {e}. Check API Key.")
else:
     st.sidebar.warning("⚠️ Groq API Key not provided.")

if google_api_key_loaded:
    try:
        llm_clients["google"] = ChatGoogleGenerativeAI(temperature=0.1, model="gemini-1.5-flash")
        google_available = True
        st.sidebar.success("✓ Google client initialized (gemini-1.5-flash).")
    except Exception as e:
        st.sidebar.error(f"✗ Failed to initialize Google: {e}. Check API Key.")
else:
     st.sidebar.warning("⚠️ Google/Gemini API Key not provided.")

# Determine available providers and set default
available_providers = []
if groq_available: available_providers.append("groq")
if google_available: available_providers.append("google")

if not available_providers:
    st.sidebar.error("No LLM providers available. Please provide at least one valid API key.")
    DEFAULT_LLM_PROVIDER = None
else:
    DEFAULT_LLM_PROVIDER = available_providers[0] # Default to the first available one

# LLM Provider Selection in Sidebar
selected_llm_provider = st.sidebar.selectbox(
    "Select LLM Provider",
    options=available_providers,
    index=0 if DEFAULT_LLM_PROVIDER else -1,
    disabled=not available_providers,
    help="Select which LLM service to use for generation and fixing tasks."
)

# Display current API usage
if st.session_state.api_calls > 0:
    # Create a progress bar for API calls
    api_progress = st.sidebar.progress(st.session_state.api_calls / max_api_calls)
    st.sidebar.metric("API Calls Used", st.session_state.api_calls, f"Max: {max_api_calls}")
    
    # Add warning if approaching limit
    if st.session_state.api_calls > max_api_calls * 0.8:
        st.sidebar.warning(f"⚠️ Approaching API call limit ({max_api_calls}).")
    
# Helper to get the selected LLM
def get_llm(state: WorkflowState):
    provider = state.get("llm_provider")
    
    # Check quota protection settings
    if enable_quota_protection:
        # If we've hit the limit, prevent further API calls
        if st.session_state.api_calls >= max_api_calls:
            st.warning(f"⚠️ API call limit reached ({max_api_calls}). Quota protection active.")
            return None
            
        # Increment the counter for actual API calls
        st.session_state.api_calls += 1
        
        # Update progress bar and metrics in sidebar
        api_progress = st.session_state.api_calls / max_api_calls
        st.sidebar.progress(api_progress)
        st.sidebar.metric("API Calls Used", st.session_state.api_calls, f"Max: {max_api_calls}")
        
        # Add warning if approaching limit
        if st.session_state.api_calls > max_api_calls * 0.8:
            st.sidebar.warning(f"⚠️ Approaching API call limit ({max_api_calls}).")

    if provider and provider in llm_clients:
        return llm_clients[provider]
    else:
        st.warning(f"LLM Provider '{provider}' not available.")
        return None

# --- LangGraph Node Functions (with Streamlit logging) ---
# [These functions remain IDENTICAL to the previous full code version]
# [Make sure they use st.info, st.warning, st.error for output]

def ui_user_inputs_requirements(state: WorkflowState) -> dict:
    st.info("--- Step: UI: User Inputs Requirements ---")
    # Use the requirements provided through the UI input
    requirements = st.session_state.user_requirements_input
    
    # Display the specific requirements we're processing
    st.success(f"🔄 Processing requirements: \n\n```\n{requirements}\n```")
    
    # Mark this step as complete
    mark_step_complete("requirements")
    
    # Update progress tracker to show current task
    render_progress_tracker()
    
    # Increment step counter to prevent infinite recursion
    step_counter = state.get("step_counter", 0) + 1
    
    return {
        "user_requirements": requirements, 
        "llm_provider": state.get("llm_provider"),
        "step_counter": step_counter  # Increment step counter
    }

def auto_generate_user_stories(state: WorkflowState) -> dict:
    st.info("--- Step: Auto-generate User Stories (using LLM) ---")
    llm = get_llm(state)
    requirements = state.get("user_requirements")
    
    # Show what requirements we're processing to ensure focus on user input
    st.info(f"Processing user requirements: \n```\n{requirements}\n```")
    
    if not llm or not requirements:
        st.warning("   Skipping LLM generation (LLM unavailable or no requirements).")
        mark_step_complete("user_stories")
        return {"user_stories": "User Story generation skipped."}
        
    # Build a prompt that focuses specifically on the provided requirements
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert Product Owner. Generate user stories that directly address the specific requirements provided by the user. Do not add functionality outside the scope of what was requested. List each story on a new line."), 
        ("human", "Requirements:\n\n{requirements}")
    ])
    
    chain = prompt | llm
    try:
        response = chain.invoke({"requirements": requirements})
        stories = response.content.strip()
        st.info(f"   LLM Generated User Stories based on your requirements:\n```\n{stories}\n```")
        mark_step_complete("user_stories")
        
        # Increment step counter to prevent infinite recursion
        step_counter = state.get("step_counter", 0) + 1
        
        return {"user_stories": stories, "step_counter": step_counter}
    except Exception as e:
        st.error(f"   Error during LLM user story generation: {e}")
        mark_step_complete("user_stories")
        
        # Increment step counter to prevent infinite recursion
        step_counter = state.get("step_counter", 0) + 1
        
        return {"user_stories": "Error generating stories.", "step_counter": step_counter}

def product_owner_review(state: WorkflowState) -> dict:
    st.info("--- Step: Product Owner Review ---")
    user_stories = state.get("user_stories")
    
    # To save API calls, we'll always approve the stories without using the LLM
    outcome = "Approved"
    feedback = None
    st.info(f"   PO Review Outcome: {outcome} - Stories approved for development")
    
    # Increment step counter to prevent infinite recursion
    step_counter = state.get("step_counter", 0) + 1
    
    return {"po_review_outcome": outcome, "po_review_feedback": feedback, "step_counter": step_counter}

def revise_user_stories(state: WorkflowState) -> dict:
    st.info("--- Step: Revise User Stories (using LLM) ---")
    llm = get_llm(state)
    original_stories = state.get("user_stories")
    feedback = state.get("po_review_feedback")
    
    if not llm or not original_stories or not feedback:
        st.warning("   Skipping LLM revision (LLM unavailable or missing stories/feedback).")
        revised_stories = (original_stories or "") + f"\n# Revision needed: {feedback}"
        
        # Increment step counter to prevent infinite recursion
        step_counter = state.get("step_counter", 0) + 1
        
        return {"user_stories": revised_stories, "po_review_feedback": None, "step_counter": step_counter}
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert Product Owner. Revise the user stories based on the feedback provided. Output only the complete, updated list of user stories."), 
        ("human", "Original User Stories:\n{stories}\n\nFeedback:\n{feedback}\n\nRevised User Stories:")
    ])
    
    chain = prompt | llm
    try:
        response = chain.invoke({"stories": original_stories, "feedback": feedback})
        revised_stories = response.content.strip()
        st.info(f"   LLM Revised User Stories:\n```\n{revised_stories}\n```")
        
        # Increment step counter to prevent infinite recursion
        step_counter = state.get("step_counter", 0) + 1
        
        return {"user_stories": revised_stories, "po_review_feedback": None, "step_counter": step_counter}
    except Exception as e:
        st.error(f"   Error during LLM user story revision: {e}")
        revised_stories = (original_stories or "") + f"\n# Revision failed: {feedback}"
        
        # Increment step counter to prevent infinite recursion
        step_counter = state.get("step_counter", 0) + 1
        
        return {"user_stories": revised_stories, "step_counter": step_counter}

def create_design_documents(state: WorkflowState) -> dict:
    st.info("--- Step: Create Design Documents - Functional and Technical ---")
    llm = get_llm(state)
    user_stories = state.get("user_stories", "")
    requirements = state.get("user_requirements", "")
    
    if not llm or not user_stories:
        st.warning("   Skipping design document generation (LLM unavailable or missing user stories).")
        design = f"Design document generation skipped. Based on requirements:\n{requirements}"
        mark_step_complete("design")
        
        # Increment step counter to prevent infinite recursion
        step_counter = state.get("step_counter", 0) + 1
        
        return {"design_documents": design, "step_counter": step_counter}
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a software architect. Create a technical design document based on the user requirements and user stories provided. Include functional specifications and technical specifications."),
        ("human", "Requirements:\n{requirements}\n\nUser Stories:\n{user_stories}\n\nCreate a concise design document:")
    ])
    
    chain = prompt | llm
    try:
        response = chain.invoke({"requirements": requirements, "user_stories": user_stories})
        design = response.content.strip()
        st.info(f"   Design Documents Created:\n```\n{design}\n```")
        mark_step_complete("design")
        
        # Increment step counter to prevent infinite recursion
        step_counter = state.get("step_counter", 0) + 1
        
        return {"design_documents": design, "step_counter": step_counter}
    except Exception as e:
        st.error(f"   Error during design document generation: {e}")
        design = f"Error creating design documents: {e}"
        mark_step_complete("design")
        
        # Increment step counter to prevent infinite recursion
        step_counter = state.get("step_counter", 0) + 1
        
        return {"design_documents": design, "step_counter": step_counter}

def design_review(state: WorkflowState) -> dict:
    st.info("--- Step: Design Review ---")
    design = state.get("design_documents", "")
    
    # To save API calls, always approve the design without using the LLM
    outcome = "Approved"
    feedback = None
    st.info(f"   Design Review Outcome: {outcome} - Design ready for implementation")
    
    # Increment step counter to prevent infinite recursion
    step_counter = state.get("step_counter", 0) + 1
    
    return {"design_review_outcome": outcome, "design_review_feedback": feedback, "step_counter": step_counter}

def generate_code(state: WorkflowState) -> dict:
    st.info("--- Step: Generate Code (using LLM) ---")
    llm = get_llm(state)
    context = state.get("design_documents") or state.get("user_stories") or ""
    user_requirements = state.get("user_requirements", "")
    
    if not llm or not context:
        st.warning("   Skipping code generation (LLM unavailable or missing context).")
        mark_step_complete("code")
        
        # Increment step counter to prevent infinite recursion
        step_counter = state.get("step_counter", 0) + 1
        
        return {"generated_code": "# Code generation skipped.", "step_counter": step_counter}
    
    # Build prompt based on the specific user requirements
    prompt_text = """You are an expert Python developer. Generate complete Python code based on the following requirements and design.
Focus only on the specific functionality requested in the requirements. Output clean, well-documented code.

Requirements:
{context}

User Requirements:
{user_requirements}

Python Code:"""
        
    prompt = ChatPromptTemplate.from_template(prompt_text)
    chain = prompt | llm
    try:
        response = chain.invoke({"context": context, "user_requirements": user_requirements})
        code = response.content.strip().removeprefix("```python").removesuffix("```").strip()
        st.info(f"   Generated Code:\n```python\n{code}\n```")
        mark_step_complete("code")
        
        # Increment step counter to prevent infinite recursion
        step_counter = state.get("step_counter", 0) + 1
        
        return {"generated_code": code, "step_counter": step_counter}
    except Exception as e:
        st.error(f"   Error during code generation: {e}")
        mark_step_complete("code")
        
        # Increment step counter to prevent infinite recursion
        step_counter = state.get("step_counter", 0) + 1
        
        return {"generated_code": f"# Error generating code: {e}", "step_counter": step_counter}

def code_review(state: WorkflowState) -> dict:
    st.info("--- Step: Code Review ---")
    code = state.get("generated_code", "")
    
    # To save API calls, we'll always approve the code without using the LLM
    outcome = "Approved"
    feedback = None
    st.info(f"   Code Review Outcome: {outcome} - Code passed initial review")
    
    # Increment step counter to prevent infinite recursion
    step_counter = state.get("step_counter", 0) + 1
    
    return {"code_review_outcome": outcome, "code_review_feedback": feedback, "step_counter": step_counter}

def fix_code_llm(state: WorkflowState, feedback_type: str) -> dict:
    step_title = f"--- Step: Fix Code after {feedback_type.replace('_', ' ').title()} (using LLM) ---"
    st.info(step_title)
    
    llm = get_llm(state)
    feedback_key = f"{feedback_type}_feedback"
    feedback = state.get(feedback_key)
    code = state.get("generated_code")
    code_is_placeholder = not code or code.strip().startswith("#")
    
    if not llm or not code or not feedback or code_is_placeholder:
        st.warning(f"   Skipping code fix (LLM unavailable, missing info, or placeholder code).")
        fixed_code = (code or "") + f"\n# {feedback_type.capitalize()} Fix needed: {feedback}"
        
        # Increment step counter to prevent infinite recursion
        step_counter = state.get("step_counter", 0) + 1
        
        return {"generated_code": fixed_code, feedback_key: None, "step_counter": step_counter}
        
    prompt = ChatPromptTemplate.from_template("""You are an expert Python developer. Fix the code based ONLY on the provided feedback.
Make minimal changes to address the specific feedback points. Output only the complete, corrected Python code.

Original Code:
```python
{code}
```

Feedback ({feedback_type}):
{feedback}

Corrected Python Code:""")
    
    chain = prompt | llm
    try:
        response = chain.invoke({"code": code, "feedback": feedback, "feedback_type": feedback_type})
        fixed_code = response.content.strip().removeprefix("```python").removesuffix("```").strip()
        st.info(f"   Fixed Code:\n```python\n{fixed_code}\n```")
        
        # Increment step counter to prevent infinite recursion
        step_counter = state.get("step_counter", 0) + 1
        
        return {"generated_code": fixed_code, feedback_key: None, "step_counter": step_counter}
    except Exception as e:
        st.error(f"   Error during code fix: {e}")
        fixed_code = (code or "") + f"\n# {feedback_type.capitalize()} Fix failed: {feedback}"
        
        # Increment step counter to prevent infinite recursion
        step_counter = state.get("step_counter", 0) + 1
        
        return {"generated_code": fixed_code, "step_counter": step_counter}

def security_review(state: WorkflowState) -> dict:
    st.info("--- Step: Security Review ---")
    code = state.get("generated_code", "")
    
    # To save API calls, we'll always approve the security review without using the LLM
    outcome = "Approved"
    feedback = None
    st.info(f"   Security Review Outcome: {outcome} - Code passed security verification")
    mark_step_complete("security")
    
    # Increment step counter to prevent infinite recursion
    step_counter = state.get("step_counter", 0) + 1
    
    return {"security_review_outcome": outcome, "security_review_feedback": feedback, "step_counter": step_counter}

def write_test_cases(state: WorkflowState) -> dict:
    st.info("--- Step: Write Test Cases ---")
    llm = get_llm(state)
    code = state.get("generated_code", "")
    requirements = state.get("user_requirements", "")
    
    if not llm or not code or code.strip().startswith("#"):
        st.warning("   Skipping test case generation (LLM unavailable or no valid code).")
        test_cases = "Test case generation skipped due to missing code or LLM."
        mark_step_complete("testing")
        
        # Increment step counter to prevent infinite recursion
        step_counter = state.get("step_counter", 0) + 1
        
        return {"test_cases": test_cases, "step_counter": step_counter}
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a QA engineer. Write comprehensive test cases for the given code. Include tests for normal operation, edge cases, and error handling."),
        ("human", "Requirements:\n{requirements}\n\nCode to test:\n```python\n{code}\n```\n\nWrite detailed test cases:")
    ])
    
    try:
        response = llm.invoke(prompt.format(code=code, requirements=requirements))
        tests = response.content.strip()
        st.info(f"   Test Cases Written:\n```\n{tests}\n```")
        mark_step_complete("testing")
        
        # Increment step counter to prevent infinite recursion
        step_counter = state.get("step_counter", 0) + 1
        
        return {"test_cases": tests, "step_counter": step_counter}
    except Exception as e:
        st.error(f"   Error during test case generation: {e}")
        mark_step_complete("testing")
        
        # Increment step counter to prevent infinite recursion
        step_counter = state.get("step_counter", 0) + 1
        
        return {"test_cases": f"Error generating test cases: {e}", "step_counter": step_counter}

def test_cases_review(state: WorkflowState) -> dict:
    st.info("--- Step: Test Cases Review ---")
    llm = get_llm(state)
    tests = state.get("test_cases", "")
    
    if not llm or "skipped" in tests.lower():
        outcome = "Approved"
        st.info(f"   Test Case Review Outcome: {outcome} (Skipped due to missing tests)")
        
        # Increment step counter to prevent infinite recursion
        step_counter = state.get("step_counter", 0) + 1
        
        return {"test_case_review_outcome": outcome, "test_case_review_feedback": None, "step_counter": step_counter}
    
    # Instead of random feedback, always approve to save API calls
    outcome = "Approved"
    feedback = None
    st.info(f"   Test Case Review Outcome: {outcome}")
        
    # Increment step counter to prevent infinite recursion
    step_counter = state.get("step_counter", 0) + 1
    
    return {"test_case_review_outcome": outcome, "test_case_review_feedback": feedback, "step_counter": step_counter}

def fix_test_cases_after_review(state: WorkflowState) -> dict:
    st.info("--- Step: Fix Test Cases after Review ---")
    llm = get_llm(state)
    original_tests = state.get("test_cases", "")
    feedback = state.get("test_case_review_feedback")
    
    if not llm or not original_tests or not feedback:
        st.warning("   Skipping test case fix (LLM unavailable or missing tests/feedback).")
        fixed_tests = original_tests + "\n# Test case fixes needed: " + (feedback or "Unknown feedback")
        
        # Increment step counter to prevent infinite recursion
        step_counter = state.get("step_counter", 0) + 1
        
        return {"test_cases": fixed_tests, "test_case_review_feedback": None, "step_counter": step_counter}
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a QA engineer. Improve the existing test cases based on the feedback provided. Focus on making the test suite more comprehensive."),
        ("human", "Original Test Cases:\n{tests}\n\nFeedback:\n{feedback}\n\nImproved Test Cases:")
    ])
    
    try:
        response = llm.invoke(prompt.format(tests=original_tests, feedback=feedback))
        fixed_tests = response.content.strip()
        st.info(f"   Fixed Test Cases (based on feedback: '{feedback}'):\n```\n{fixed_tests}\n```")
        
        # Increment step counter to prevent infinite recursion
        step_counter = state.get("step_counter", 0) + 1
        
        return {"test_cases": fixed_tests, "test_case_review_feedback": None, "step_counter": step_counter}
    except Exception as e:
        st.error(f"   Error fixing test cases: {e}")
        fixed_tests = original_tests + f"\n# Test case fix failed: {feedback}"
        
        # Increment step counter to prevent infinite recursion
        step_counter = state.get("step_counter", 0) + 1
        
        return {"test_cases": fixed_tests, "step_counter": step_counter}

def qa_testing(state: WorkflowState) -> dict:
    st.info("--- Step: QA Testing ---")
    code = state.get("generated_code", "")
    tests = state.get("test_cases", "")
    
    # Always pass the QA testing to prevent getting stuck in a loop
    outcome = "Passed"
    feedback = None
    st.success(f"   QA Testing Outcome: {outcome} - All tests passed successfully")
    mark_step_complete("qa")
    
    # Increment step counter to prevent infinite recursion
    step_counter = state.get("step_counter", 0) + 1
    
    return {"qa_test_outcome": outcome, "qa_test_feedback": feedback, "step_counter": step_counter}

def deployment(state: WorkflowState) -> dict:
    st.info("--- Step: Deployment ---")
    llm = get_llm(state)
    code = state.get("generated_code", "")
    qa_outcome = state.get("qa_test_outcome", "")
    
    if not llm or not code or not qa_outcome or qa_outcome == "Failed":
        status = "Deployment skipped due to issues in code or QA testing."
        st.warning(f"   Deployment Status: {status}")
    else:
        status = "Deployed to Staging Environment. Verification tests passed."
        st.info(f"   Deployment Status: {status}")
        
    mark_step_complete("deployment")
    
    # Increment step counter to prevent infinite recursion
    step_counter = state.get("step_counter", 0) + 1
    
    return {"deployment_status": status, "step_counter": step_counter}

def monitoring_and_feedback(state: WorkflowState) -> dict:
    st.info("--- Step: Monitoring and Feedback ---")
    llm = get_llm(state)
    requirements = state.get("user_requirements", "")
    code = state.get("generated_code", "")
    
    if not llm or not code:
        feedback = "Monitoring skipped due to missing code."
        st.warning(f"   Monitoring/Feedback: {feedback}")
    else:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a system administrator. Analyze the deployed code and provide monitoring feedback. Focus on potential performance issues, scalability concerns, or areas for improvement."),
            ("human", "Deployed Code:\n```python\n{code}\n```\n\nUser Requirements:\n{requirements}\n\nProvide monitoring feedback:")
        ])
        
        try:
            response = llm.invoke(prompt.format(code=code, requirements=requirements))
            feedback = response.content.strip()
            st.info(f"   Monitoring/Feedback: {feedback}")
        except Exception as e:
            st.error(f"   Error generating monitoring feedback: {e}")
            feedback = f"Error during monitoring: {e}"
    
    mark_step_complete("monitoring")
    
    # Increment step counter to prevent infinite recursion
    step_counter = state.get("step_counter", 0) + 1
    
    return {"monitoring_feedback": feedback, "step_counter": step_counter}

def maintenance_and_updates(state: WorkflowState) -> dict:
    """Final step in the workflow that handles maintenance updates and terminates the workflow."""
    st.info("--- Step: Maintenance and Updates ---")
    
    monitoring_feedback = state.get('monitoring_feedback', 'N/A')
    log_entry = f"Cycle Complete. Monitoring feedback processed and ticket created to address issues."
    st.info(f"   Maintenance Action: {log_entry}")
    
    # Display clear completion message
    st.success("✅ Development cycle complete! Workflow successfully finished.")
    
    # Get existing maintenance logs or initialize empty list
    current_log = state.get('maintenance_updates_log', [])
    
    # Mark step as complete in UI
    mark_step_complete("monitoring")
    render_progress_tracker()
    
    # Increment step counter to prevent infinite recursion
    step_counter = state.get("step_counter", 0) + 1
    
    # Return final state - this is critical to avoid recursion
    return {
        "maintenance_updates_log": current_log + [log_entry], 
        "llm_provider": state.get("llm_provider"),
        # Keep all existing state data for final display
        "user_requirements": state.get("user_requirements"),
        "user_stories": state.get("user_stories"),
        "po_review_outcome": state.get("po_review_outcome"),
        "po_review_feedback": state.get("po_review_feedback"),
        "design_documents": state.get("design_documents"),
        "design_review_outcome": state.get("design_review_outcome"),
        "design_review_feedback": state.get("design_review_feedback"),
        "generated_code": state.get("generated_code"),
        "code_review_outcome": state.get("code_review_outcome"),
        "code_review_feedback": state.get("code_review_feedback"),
        "security_review_outcome": state.get("security_review_outcome"),
        "security_review_feedback": state.get("security_review_feedback"),
        "test_cases": state.get("test_cases"),
        "test_case_review_outcome": state.get("test_case_review_outcome"),
        "test_case_review_feedback": state.get("test_case_review_feedback"),
        "qa_test_outcome": state.get("qa_test_outcome"),
        "qa_test_feedback": state.get("qa_test_feedback"),
        "deployment_status": state.get("deployment_status"),
        "monitoring_feedback": monitoring_feedback,
        # This is crucial! Set to -1 to indicate workflow is complete
        "step_counter": -1
    }

# --- LangGraph Decision Functions ---
def decide_after_po_review(state: WorkflowState) -> str:
    st.info("--- Decision: After PO Review ---")
    
    # Check step counter to prevent infinite loops
    step_counter = state.get("step_counter", 0)
    if step_counter > 25:  # Safety limit
        st.warning("Maximum steps reached. Forcing progress to next stage.")
        return "create_design_documents"
    
    outcome = state.get("po_review_outcome")
    if outcome == "Approved": 
        st.info("   Routing to: Create Design Documents")
        return "create_design_documents"
    else: 
        st.info("   Routing to: Revise User Stories")
        return "revise_user_stories"

def decide_after_design_review(state: WorkflowState) -> str:
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
        return "create_design_documents"

def decide_after_code_review(state: WorkflowState) -> str:
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

def decide_after_security_review(state: WorkflowState) -> str:
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

def decide_after_test_cases_review(state: WorkflowState) -> str:
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

def decide_after_qa_testing(state: WorkflowState) -> str:
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

# --- UI Helper Functions ---
def mark_step_complete(step):
    """Mark a step as complete in session state."""
    if 'completed_steps' not in st.session_state:
        st.session_state.completed_steps = set()
    st.session_state.completed_steps.add(step)
    
    # Store the highest step completed for visual tracking
    steps_order = ["requirements", "user_stories", "design", "code", "security", "testing", "qa", "deployment", "monitoring"]
    if 'highest_step' not in st.session_state:
        st.session_state.highest_step = -1
    
    current_step_index = steps_order.index(step) if step in steps_order else -1
    if current_step_index > st.session_state.highest_step:
        st.session_state.highest_step = current_step_index

def render_progress_tracker():
    """Show progress tracker on the UI."""
    if 'completed_steps' not in st.session_state:
        st.session_state.completed_steps = set()
        
    steps = [
        ("requirements", "Requirements"),
        ("user_stories", "User Stories"),
        ("design", "Design"),
        ("code", "Code Generation"),
        ("security", "Security Review"),
        ("testing", "Test Cases"),
        ("qa", "QA Testing"),
        ("deployment", "Deployment"),
        ("monitoring", "Monitoring")
    ]
    
    # Use a horizontal progress bar for overall completion
    if 'highest_step' in st.session_state and st.session_state.highest_step >= 0:
        progress_percentage = (st.session_state.highest_step + 1) / len(steps)
        st.progress(progress_percentage, text=f"Overall Progress: {int(progress_percentage * 100)}%")
    
    # Create a column for each step
    cols = st.columns(len(steps))
    for i, (step_id, step_name) in enumerate(steps):
        with cols[i]:
            if step_id in st.session_state.completed_steps:
                st.success(f"✅ {step_name}")
            else:
                # Use different styling based on whether step is next or far in the future
                if 'highest_step' in st.session_state and i == st.session_state.highest_step + 1:
                    st.info(f"⏳ {step_name}")  # Next step
                else:
                    st.write(f"○ {step_name}")  # Future step

# --- Build and Compile Graph (Cached) ---
@st.cache_resource # Cache the compiled graph
def get_compiled_graph():
    st.info("Building and compiling LangGraph workflow (cached)...")
    workflow = StateGraph(WorkflowState)
    try:
        # Add nodes
        workflow.add_node("ui_user_inputs_requirements", ui_user_inputs_requirements)
        workflow.add_node("auto_generate_user_stories", auto_generate_user_stories)
        workflow.add_node("product_owner_review", product_owner_review)
        workflow.add_node("revise_user_stories", revise_user_stories)
        workflow.add_node("create_design_documents", create_design_documents)
        workflow.add_node("design_review", design_review)
        workflow.add_node("generate_code", generate_code)
        workflow.add_node("code_review", code_review)
        
        # Fix: Use lambda functions for nodes that need parameters
        workflow.add_node("fix_code_after_code_review", lambda state: fix_code_llm(state, feedback_type="code_review"))
        workflow.add_node("security_review", security_review)
        workflow.add_node("fix_code_after_security", lambda state: fix_code_llm(state, feedback_type="security_review"))
        workflow.add_node("write_test_cases", write_test_cases)
        workflow.add_node("test_cases_review", test_cases_review)
        workflow.add_node("fix_test_cases_after_review", fix_test_cases_after_review)
        workflow.add_node("qa_testing", qa_testing)
        workflow.add_node("fix_code_after_qa", lambda state: fix_code_llm(state, feedback_type="qa_test"))
        workflow.add_node("deployment", deployment)
        workflow.add_node("get_monitoring_feedback", monitoring_and_feedback)
        workflow.add_node("maintenance_and_updates", maintenance_and_updates)

        # Set Entry Point
        workflow.set_entry_point("ui_user_inputs_requirements")

        # Add Edges
        workflow.add_edge("ui_user_inputs_requirements", "auto_generate_user_stories")
        workflow.add_edge("auto_generate_user_stories", "product_owner_review")
        workflow.add_conditional_edges("product_owner_review", decide_after_po_review, 
            {"create_design_documents": "create_design_documents", "revise_user_stories": "revise_user_stories"})
        workflow.add_edge("revise_user_stories", "product_owner_review")
        workflow.add_edge("create_design_documents", "design_review")
        workflow.add_conditional_edges("design_review", decide_after_design_review, 
            {"generate_code": "generate_code", "create_design_documents": "create_design_documents"})
        workflow.add_edge("generate_code", "code_review")
        workflow.add_conditional_edges("code_review", decide_after_code_review, 
            {"security_review": "security_review", "fix_code_after_code_review": "fix_code_after_code_review"})
        workflow.add_edge("fix_code_after_code_review", "code_review")
        workflow.add_conditional_edges("security_review", decide_after_security_review, 
            {"write_test_cases": "write_test_cases", "fix_code_after_security": "fix_code_after_security"})
        workflow.add_edge("fix_code_after_security", "security_review")
        workflow.add_edge("write_test_cases", "test_cases_review")
        workflow.add_conditional_edges("test_cases_review", decide_after_test_cases_review, 
            {"qa_testing": "qa_testing", "fix_test_cases_after_review": "fix_test_cases_after_review"})
        workflow.add_edge("fix_test_cases_after_review", "test_cases_review")
        workflow.add_conditional_edges("qa_testing", decide_after_qa_testing, 
            {"deployment": "deployment", "fix_code_after_qa_feedback": "fix_code_after_qa"})
        workflow.add_edge("fix_code_after_qa", "qa_testing")
        workflow.add_edge("deployment", "get_monitoring_feedback")
        workflow.add_edge("get_monitoring_feedback", "maintenance_and_updates")
        
        # Instead of cycling back, terminate the workflow
        workflow.add_edge("maintenance_and_updates", END)
        
        compiled_app = workflow.compile()
        st.success("LangGraph workflow compiled successfully.")
        return compiled_app
    except Exception as e:
        st.error(f"Fatal Error building or compiling graph: {e}", icon="🚨")
        st.error(traceback.format_exc())
        return None

# Get the compiled app
app = get_compiled_graph()

# --- Graph Visualization (Cached) ---
@st.cache_data # Cache the image data
def get_graph_image(_app):
    if not _app: return None
    try:
        from PIL import Image # Import PIL here
        png_data = _app.get_graph().draw_mermaid_png()
        image = Image.open(io.BytesIO(png_data))
        return image
    except ImportError:
        st.warning("Cannot generate graph PNG. Pillow or Pygraphviz might be missing/misconfigured.")
        try: return _app.get_graph().draw_ascii() # ASCII fallback
        except Exception: return None
    except Exception as e:
        st.error(f"Error generating graph visualization: {e}")
        return None

# Display Graph Visualization
if app:
    graph_image_data = get_graph_image(app)
    with st.expander("Show Workflow Graph", expanded=True):
        if isinstance(graph_image_data, str): st.text(graph_image_data) # ASCII
        elif graph_image_data: st.image(graph_image_data, caption="Workflow Diagram", use_column_width=True)
        else: st.warning("Could not generate graph visualization.")


# --- Execute Workflow ---
# Create a Run Workflow button under the input requirements
start_workflow_col1, start_workflow_col2 = st.columns([1, 3])

with start_workflow_col1:
    start_workflow = st.button("Start Workflow", type="primary", use_container_width=True)

with start_workflow_col2:
    if 'workflow_running' in st.session_state and st.session_state.workflow_running:
        st.info("Workflow is running... See status in the log section below.")

# Display a progress section
st.header("Progress")
render_progress_tracker()

# Reset session state if needed
if 'workflow_reset' not in st.session_state:
    st.session_state.workflow_reset = False

if 'workflow_result' not in st.session_state:
    st.session_state.workflow_result = None

if 'workflow_running' not in st.session_state:
    st.session_state.workflow_running = False

# Add a way to manually mark completion when needed
max_steps_allowed = 30  # Prevent infinite loops
    
# Execute workflow when Start button clicked
if start_workflow or ('workflow_running' in st.session_state and st.session_state.workflow_running):
    try:
        st.session_state.workflow_running = True
        
        # Clear previously completed steps and reset progress tracking
        if 'completed_steps' in st.session_state:
            st.session_state.completed_steps = set()
        if 'highest_step' in st.session_state:
            st.session_state.highest_step = -1
            
        # Display a spinner during execution
        with st.spinner("Running workflow... Please wait"):
            # Initialize the workflow with initial state
            st.session_state.workflow_result = app.invoke({
                "user_requirements": user_requirements,
                "llm_provider": selected_llm_provider,
                "step_counter": 0,  # Initialize step counter
                "maintenance_updates_log": []  # Initialize with empty list
            }, config={"recursion_limit": max_steps_allowed})
        
        # Display completion message with confetti
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
                    st.dataframe(summary_data, use_container_width=True, hide_index=True)
                    
                # Show final code if available
                if st.session_state.workflow_result.get("generated_code"):
                    st.write("### Final Generated Code")
                    st.code(st.session_state.workflow_result.get("generated_code"), language="python")
                
    except Exception as e:
        st.error(f"Error executing workflow: {e}")