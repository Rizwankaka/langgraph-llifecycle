"""
LLM provider utilities and client management.
"""
import os
import streamlit as st
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

# LLM clients cache
llm_clients = {}
groq_available = False
google_available = False
DEFAULT_LLM_PROVIDER = None

def initialize_llm_clients():
    """Initialize LLM clients based on available API keys"""
    global llm_clients, groq_available, google_available, DEFAULT_LLM_PROVIDER
    
    # Load API keys from environment
    groq_api_key_loaded = os.environ.get("GROQ_API_KEY", "")
    google_api_key_loaded = os.environ.get("GOOGLE_API_KEY", "")
    
    # Initialize Groq client if API key available
    if groq_api_key_loaded:
        try:
            llm_clients["groq"] = ChatGroq(temperature=0.1, model_name="llama3-8b-8192")
            groq_available = True
            st.sidebar.success("✓ Groq client initialized (llama3-8b).")
        except Exception as e:
            st.sidebar.error(f"✗ Failed to initialize Groq: {e}. Check API Key.")
    else:
        st.sidebar.warning("⚠️ Groq API Key not provided.")

    # Initialize Google client if API key available
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
        DEFAULT_LLM_PROVIDER = available_providers[0]
    
    return available_providers

def get_llm(state):
    """Get the LLM client based on the state"""
    provider = state.get("llm_provider")
    
    # Check quota protection settings
    if st.session_state.get('enable_quota_protection', True):
        max_api_calls = st.session_state.get('max_api_calls', 25)
        
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