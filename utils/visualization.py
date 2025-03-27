"""
Graph visualization utilities.
"""
import streamlit as st
import networkx as nx
import io
from PIL import Image
from config.settings import GRAPH_HEIGHT, GRAPH_WIDTH

def generate_workflow_graph(workflow_graph):
    """Convert a LangGraph graph to a visualization using mermaid"""
    if not workflow_graph:
        return None
    
    try:
        # Use LangGraph's built-in visualization method
        png_data = workflow_graph.get_graph().draw_mermaid_png()
        
        # Convert PNG data to image
        image = Image.open(io.BytesIO(png_data))
        return image
    except Exception as e:
        st.error(f"Error generating graph visualization: {e}")
        # Fallback to ASCII visualization if PNG fails
        try:
            return workflow_graph.get_graph().draw_ascii()
        except Exception:
            return None

def display_workflow_graph(graph_image):
    """Display a workflow graph in Streamlit"""
    if graph_image is None:
        st.warning("No workflow graph available to display.")
        return
    
    try:
        if isinstance(graph_image, str):
            # Display ASCII visualization
            st.text(graph_image)
        else:
            # Display image
            st.image(graph_image, caption="Workflow Diagram", use_column_width=True)
    except Exception as e:
        st.error(f"Error displaying workflow graph: {e}")