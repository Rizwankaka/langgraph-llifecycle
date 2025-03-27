"""
Sidebar UI components and configuration.
"""
import streamlit as st
import os
from utils.llm import initialize_llm_clients

def setup_sidebar():
    """Setup the sidebar with API configuration and provider selection"""
    st.sidebar.header("API Configuration")

    # Load API keys from environment
    groq_api_key_loaded = os.environ.get("GROQ_API_KEY", "")
    google_api_key_loaded = os.environ.get("GOOGLE_API_KEY", "")

    # API key inputs in sidebar
    with st.sidebar.expander("API Keys", expanded=True):
        groq_api_key = st.text_input(
            "Groq API Key", 
            value=groq_api_key_loaded,
            type="password",
            help="Enter your Groq API key"
        )
        
        google_api_key = st.text_input(
            "Google/Gemini API Key", 
            value=google_api_key_loaded,
            type="password",
            help="Enter your Google/Gemini API key"
        )

    # Update environment variables with user-provided keys if entered
    if groq_api_key and groq_api_key != groq_api_key_loaded:
        os.environ["GROQ_API_KEY"] = groq_api_key
        groq_api_key_loaded = groq_api_key

    if google_api_key and google_api_key != google_api_key_loaded:
        os.environ["GOOGLE_API_KEY"] = google_api_key
        google_api_key_loaded = google_api_key

    # Initialize LLM clients
    available_providers = initialize_llm_clients()

    # API Usage Protection
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
        value=25,
        help="Set a maximum limit for API calls to prevent quota exhaustion"
    )

    # Initialize session state variables if not already set
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
        # Use st.rerun() instead of the deprecated st.experimental_rerun()
        st.rerun()

    # Display current API usage if calls have been made
    if st.session_state.api_calls > 0:
        api_progress = st.session_state.api_calls / max_api_calls
        st.sidebar.progress(api_progress)
        st.sidebar.metric("API Calls Used", st.session_state.api_calls, f"Max: {max_api_calls}")
        
        # Add warning if approaching limit
        if st.session_state.api_calls > max_api_calls * 0.8:
            st.sidebar.warning(f"⚠️ Approaching API call limit ({max_api_calls}).")

    # LLM Provider Selection
    selected_llm_provider = None
    if available_providers:
        default_index = 0
        selected_llm_provider = st.sidebar.selectbox(
            "Select LLM Provider",
            options=available_providers,
            index=default_index,
            disabled=not available_providers,
            help="Select which LLM service to use for generation and fixing tasks."
        )
    else:
        st.sidebar.warning("⚠️ No LLM providers available. Please enter API keys above.")
    
    # Save user selections to session state
    st.session_state.enable_quota_protection = enable_quota_protection
    st.session_state.max_api_calls = max_api_calls
    
    return selected_llm_provider