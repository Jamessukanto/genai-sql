import streamlit as st
import requests
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import (
    SAMPLE_QUESTIONS,
    append_message,
    truncate_text,
    make_api_call,
    generate_token
)

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="💬 Chat Assistant", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_fleet_id" not in st.session_state:
    st.session_state.current_fleet_id = None

if "current_token" not in st.session_state:
    st.session_state.current_token = None

# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================
def render_sidebar():
    """Render the sidebar with fleet selection and sample questions."""
    with st.sidebar:
        st.header("Configuration")
        
        # Fleet selection
        fleet_id = st.selectbox("Grant access to fleet:", options=["1", "2"])
        
        # Auto-generate token when fleet changes or when no token exists
        if fleet_id != st.session_state.current_fleet_id or st.session_state.current_token is None:
            try:
                token = generate_token(fleet_id)
                st.success(f"✅ Connected to fleet {fleet_id}")
            except Exception as e:
                st.error(f"❌ Failed to connect to fleet {fleet_id}: {str(e)}")
        
        # Sample questions section
        st.markdown("---")
        st.text("Sample Questions:")
        
        for i, question in enumerate(SAMPLE_QUESTIONS):
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.text(truncate_text(question))
                
                with col2:
                    if st.button("→", key=f"send_btn_{i}", help="Send to chat"):
                        st.session_state.pending_question = question
                        st.rerun()
        
        return fleet_id

# ============================================================================
# CHAT PROCESSING
# ============================================================================
def process_chat_query(query: str):
    """Process a chat query and get AI response."""
    append_message("human", query)
    
    try:
        with st.spinner("Thinking..."):
            token = st.session_state.current_token
            chat_response = make_api_call("api/chat/execute_user_query", {
                "messages": st.session_state.messages,
                "query": query
            }, token)
            reply = chat_response["response"]
            append_message("ai", reply)
    except Exception as e:
        st.error(str(e))

def handle_pending_question():
    """Handle any pending question from the sidebar."""
    if "pending_question" in st.session_state:
        query = st.session_state.pending_question
        del st.session_state.pending_question  # Clear immediately to prevent glitches
        process_chat_query(query)

# ============================================================================
# MAIN APPLICATION
# ============================================================================
def main():
    """Main application function."""

    st.title("SQL Chat Assistant Demo")
    
    _ = render_sidebar()
    
    handle_pending_question()
    
    query = st.chat_input("Type your message here...")
    if query:
        process_chat_query(query)
    
    # Render chat history
    for message in st.session_state.messages:
        if message["type"] == "system":
            continue
        with st.chat_message("user" if message["type"] == "human" else "assistant"):
            st.markdown(message["content"])

if __name__ == "__main__":
    main()

