"""
Cert Me Boi - Streamlit GUI
Simple web interface for course automation
"""

import streamlit as st
import yaml
import json
import time
from pathlib import Path
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Page config
st.set_page_config(
    page_title="Cert Me Boi",
    page_icon="🎓",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def load_config():
    """Load configuration"""
    try:
        config_path = Path("config/courses.yaml")
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
    except Exception as e:
        st.error(f"Failed to load config: {e}")
    return {}

def main():
    """Main application"""
    st.markdown('<h1 class="main-header">🎓 Cert Me Boi</h1>', unsafe_allow_html=True)
    st.markdown("### Automated Course Certification System")
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Dashboard", "Add Course", "Settings", "Logs"]
    )
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "Add Course":
        show_add_course()
    elif page == "Settings":
        show_settings()
    elif page == "Logs":
        show_logs()

def show_dashboard():
    """Show main dashboard"""
    st.header("📊 Dashboard")
    
    # Status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Status", "🟢 Running")
    
    with col2:
        st.metric("Active Courses", "2")
    
    with col3:
        st.metric("Certificates Earned", "12")
    
    # Quick actions
    st.subheader("Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Start New Course", type="primary"):
            st.success("Starting new course...")
    
    with col2:
        if st.button("⏸️ Pause All"):
            st.warning("Paused all courses")
    
    with col3:
        if st.button("⏹️ Stop All"):
            st.error("Stopped all courses")
    
    # Course progress
    st.subheader("Course Progress")
    
    courses = [
        {"name": "Python Basics", "progress": 75, "platform": "Coursera"},
        {"name": "Data Science", "progress": 45, "platform": "Udemy"},
        {"name": "Machine Learning", "progress": 30, "platform": "edX"}
    ]
    
    for course in courses:
        with st.expander(f"{course['name']} ({course['platform']})"):
            st.progress(course['progress'] / 100)
            st.write(f"Progress: {course['progress']}%")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Resume {course['name']}", key=f"resume_{course['name']}"):
                    st.success(f"Resumed {course['name']}")
            with col2:
                if st.button(f"Stop {course['name']}", key=f"stop_{course['name']}"):
                    st.error(f"Stopped {course['name']}")

def show_add_course():
    """Show add course form"""
    st.header("➕ Add New Course")
    
    with st.form("add_course"):
        course_url = st.text_input("Course URL")
        
        col1, col2 = st.columns(2)
        
        with col1:
            platform = st.selectbox("Platform", ["Coursera", "Udemy", "edX", "LinkedIn Learning"])
            email = st.text_input("Email")
        
        with col2:
            password = st.text_input("Password", type="password")
            auto_start = st.checkbox("Start immediately", value=True)
        
        submitted = st.form_submit_button("Add Course")
        
        if submitted:
            if course_url and email and password:
                st.success("Course added successfully!")
                if auto_start:
                    st.info("Starting automation...")
            else:
                st.error("Please fill in all required fields.")

def show_settings():
    """Show settings"""
    st.header("⚙️ Settings")
    
    config = load_config()
    
    # AI Settings
    st.subheader("🤖 AI Configuration")
    
    with st.form("ai_settings"):
        default_model = st.selectbox(
            "Default AI Model",
            ["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet", "local-model"]
        )
        
        openrouter_key = st.text_input("OpenRouter API Key", type="password")
        
        col1, col2 = st.columns(2)
        
        with col1:
            confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.8)
        
        with col2:
            max_retries = st.number_input("Max Retries", 1, 10, 3)
        
        submitted = st.form_submit_button("Save AI Settings")
        if submitted:
            st.success("AI settings saved!")
    
    # Browser Settings
    st.subheader("🌐 Browser Configuration")
    
    with st.form("browser_settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            headless = st.checkbox("Headless Mode", value=True)
            timeout = st.number_input("Timeout (seconds)", 10, 120, 30)
        
        with col2:
            user_agent = st.text_input(
                "User Agent", 
                value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
        
        submitted = st.form_submit_button("Save Browser Settings")
        if submitted:
            st.success("Browser settings saved!")

def show_logs():
    """Show logs"""
    st.header("📝 Logs")
    
    # Log level filter
    log_level = st.selectbox("Log Level", ["All", "INFO", "WARNING", "ERROR", "DEBUG"])
    
    if st.button("🔄 Refresh Logs"):
        st.rerun()
    
    # Sample logs
    logs = [
        {"timestamp": "2024-01-15 14:30:25", "level": "INFO", "message": "Automation started successfully"},
        {"timestamp": "2024-01-15 14:30:26", "level": "INFO", "message": "Logged into Coursera"},
        {"timestamp": "2024-01-15 14:30:27", "level": "WARNING", "message": "Slow page load detected"},
        {"timestamp": "2024-01-15 14:30:28", "level": "INFO", "message": "Video progress: 45%"},
        {"timestamp": "2024-01-15 14:30:29", "level": "ERROR", "message": "Failed to click element"}
    ]
    
    # Filter by level
    if log_level != "All":
        logs = [log for log in logs if log["level"] == log_level]
    
    # Display logs
    for log in logs:
        level_color = {
            "INFO": "blue",
            "WARNING": "orange", 
            "ERROR": "red",
            "DEBUG": "gray"
        }.get(log["level"], "black")
        
        st.markdown(f"""
        <div style="border-left: 3px solid {level_color}; padding-left: 10px; margin: 5px 0;">
            <strong>{log['timestamp']}</strong> [{log['level']}] {log['message']}
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 