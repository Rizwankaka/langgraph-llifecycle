"""
Application settings and constants.
"""

# App Information
APP_TITLE = "LangGraph-powered DevOps Workflow Simulator"
APP_DESCRIPTION = """
This application simulates a DevOps workflow from requirements gathering to deployment,
using LangGraph to orchestrate the steps and LLM integration to generate artifacts.
"""

# LLM Configuration
DEFAULT_TEMPERATURE = 0.1
MAX_API_CALLS_DEFAULT = 25

# Graph Visualization 
GRAPH_HEIGHT = 400
GRAPH_WIDTH = 700

# Workflow Steps
WORKFLOW_STEPS = [
    "requirements",
    "user_stories",
    "design", 
    "code",
    "security",
    "testing",
    "qa",
    "deployment",
    "monitoring"
]

# LLM Prompt Templates
REQUIREMENTS_PROMPT = """
You are a skilled business analyst responsible for gathering and documenting clear, 
concise, and unambiguous requirements for a software development project.

Based on the following high-level description, create a comprehensive 
requirements document with functional and non-functional requirements:

{user_input}

Your requirements document should include:
1. Overview
2. Functional Requirements (prioritized)
3. Non-Functional Requirements (performance, security, usability, etc.)
4. Constraints and Assumptions
5. Acceptance Criteria for each requirement

Be specific, precise, and ensure each requirement is testable.
"""

USER_STORIES_PROMPT = """
You are an Agile product owner responsible for creating user stories 
based on requirements documentation. 
Convert the following requirements into well-formatted user stories:

{user_requirements}

For each user story, include:
1. User story in standard format: "As a [type of user], I want [goal] so that [benefit]"
2. Acceptance criteria (3-5 specific, testable conditions)
3. Priority level (Must-Have, Should-Have, Could-Have, Won't-Have)
4. Story points estimate (1, 2, 3, 5, 8, 13)

Organize stories by priority and ensure each is independent, negotiable, valuable, 
estimable, small, and testable.
"""

# Additional prompt templates follow the same pattern...