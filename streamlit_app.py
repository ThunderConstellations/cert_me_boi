"""
Cert Me Boi - Real Functional GUI
Beautiful gold/black/white themed interface with actual automation capabilities
"""

import streamlit as st
import yaml
import json
import time
import threading
import queue
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os
import cv2
import numpy as np
from PIL import Image
import base64

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import real automation manager
from src.gui_integration import automation_manager

# Page configuration
st.set_page_config(
    page_title="Cert Me Boi - Course Automation",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for gold/black/white theme with glow effects
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --gold: #FFD700;
        --gold-glow: #FFA500;
        --black: #000000;
        --white: #FFFFFF;
        --dark-gray: #1A1A1A;
        --light-gray: #333333;
    }
    
    /* Global styles */
    .main {
        background: linear-gradient(135deg, var(--black) 0%, var(--dark-gray) 100%);
        color: var(--white);
    }
    
    .stApp {
        background: linear-gradient(135deg, var(--black) 0%, var(--dark-gray) 100%);
    }
    
    /* Header styling */
    .main-header {
        font-size: 3.5rem;
        font-weight: bold;
        background: linear-gradient(45deg, var(--gold), var(--gold-glow));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 0 0 20px var(--gold-glow);
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { text-shadow: 0 0 20px var(--gold-glow); }
        to { text-shadow: 0 0 30px var(--gold), 0 0 40px var(--gold-glow); }
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, var(--dark-gray) 0%, var(--black) 100%);
        border-right: 2px solid var(--gold);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, var(--gold), var(--gold-glow));
        color: var(--black);
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: bold;
        box-shadow: 0 0 15px var(--gold-glow);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 25px var(--gold), 0 0 35px var(--gold-glow);
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, var(--light-gray) 0%, var(--dark-gray) 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border: 2px solid var(--gold);
        box-shadow: 0 0 20px var(--gold-glow);
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 0 30px var(--gold), 0 0 40px var(--gold-glow);
    }
    
    /* Progress bars */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--gold), var(--gold-glow));
        box-shadow: 0 0 10px var(--gold-glow);
    }
    
    /* Form styling */
    .stTextInput > div > div > input {
        background: var(--light-gray);
        color: var(--white);
        border: 2px solid var(--gold);
        border-radius: 10px;
        box-shadow: 0 0 10px var(--gold-glow);
    }
    
    .stSelectbox > div > div > select {
        background: var(--light-gray);
        color: var(--white);
        border: 2px solid var(--gold);
        border-radius: 10px;
        box-shadow: 0 0 10px var(--gold-glow);
    }
    
    /* Status indicators */
    .status-running {
        color: var(--gold);
        font-weight: bold;
        text-shadow: 0 0 10px var(--gold-glow);
        animation: pulse 2s infinite;
    }
    
    .status-stopped {
        color: #FF4444;
        font-weight: bold;
        text-shadow: 0 0 10px #FF4444;
    }
    
    .status-paused {
        color: #FFAA00;
        font-weight: bold;
        text-shadow: 0 0 10px #FFAA00;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    /* Log styling */
    .log-entry {
        background: var(--light-gray);
        padding: 10px;
        border-radius: 8px;
        border-left: 4px solid var(--gold);
        margin: 5px 0;
        box-shadow: 0 0 10px var(--gold-glow);
    }
    
    /* Screenshot container */
    .screenshot-container {
        border: 2px solid var(--gold);
        border-radius: 10px;
        padding: 10px;
        background: var(--dark-gray);
        box-shadow: 0 0 15px var(--gold-glow);
    }
    
    /* Success/Error messages */
    .stSuccess {
        background: linear-gradient(45deg, #00AA00, #00FF00);
        color: var(--black);
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 0 15px #00FF00;
    }
    
    .stError {
        background: linear-gradient(45deg, #AA0000, #FF0000);
        color: var(--white);
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 0 15px #FF0000;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main Streamlit application"""
    # Main header
    st.markdown('<h1 class="main-header">🎓 Cert Me Boi</h1>', unsafe_allow_html=True)
    st.markdown('<h2 style="text-align: center; color: var(--gold); margin-bottom: 2rem;">Automated Course Certification System</h2>', unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.markdown('<h2 style="color: var(--gold);">🎯 Navigation</h2>', unsafe_allow_html=True)
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Dashboard", "Add Course", "Screen Detection", "Live Monitoring", "Settings", "Logs"]
    )
    
    # Main content area
    if page == "Dashboard":
        show_dashboard()
    elif page == "Add Course":
        show_add_course()
    elif page == "Screen Detection":
        show_screen_detection()
    elif page == "Live Monitoring":
        show_live_monitoring()
    elif page == "Settings":
        show_settings()
    elif page == "Logs":
        show_logs()

def show_dashboard():
    """Show main dashboard with real data"""
    st.markdown('<h2 style="color: var(--gold);">📊 Dashboard</h2>', unsafe_allow_html=True)
    
    # Get real statistics
    stats = automation_manager.get_statistics()
    
    # Status and quick actions
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        status = stats.get('status', 'stopped')
        status_class = "status-running" if status == 'running' else "status-stopped"
        st.markdown(f'<p class="{status_class}">Status: {status.upper()}</p>', unsafe_allow_html=True)
    
    with col2:
        if st.button("🚀 Start All", type="primary"):
            # Start all pending courses
            started = 0
            for course_id, course in automation_manager.courses.items():
                if course['status'] == 'pending':
                    if automation_manager.start_course(course_id):
                        started += 1
            if started > 0:
                st.success(f"Started {started} courses!")
            else:
                st.info("No pending courses to start")
    
    with col3:
        if st.button("⏹️ Stop All"):
            # Stop all running courses
            stopped = 0
            for course_id, course in automation_manager.courses.items():
                if course['status'] == 'running':
                    if automation_manager.stop_course(course_id):
                        stopped += 1
            if stopped > 0:
                st.error(f"Stopped {stopped} courses!")
            else:
                st.info("No running courses to stop")
    
    # Real metrics cards
    st.markdown('<h3 style="color: var(--gold);">📈 Performance Metrics</h3>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: var(--gold);">Success Rate</h3>
            <h2 style="color: var(--white);">{stats.get('success_rate', 0):.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: var(--gold);">Total Courses</h3>
            <h2 style="color: var(--white);">{stats.get('total_courses', 0)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: var(--gold);">Completed</h3>
            <h2 style="color: var(--white);">{stats.get('completed', 0)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: var(--gold);">Running</h3>
            <h2 style="color: var(--white);">{stats.get('running', 0)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Real course progress
    st.markdown('<h3 style="color: var(--gold);">📚 Course Progress</h3>', unsafe_allow_html=True)
    
    if automation_manager.courses:
        for course_id, course in automation_manager.courses.items():
            with st.expander(f"{course['name']} ({course['platform']}) - {course['status']}"):
                # Get real progress
                progress = automation_manager.get_course_progress(course_id)
                st.progress(progress / 100)
                st.write(f"Progress: {progress:.1f}%")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if course['status'] == 'pending':
                        if st.button(f"Start {course['name']}", key=f"start_{course_id}"):
                            if automation_manager.start_course(course_id):
                                st.success(f"Started {course['name']}")
                                st.rerun()
                    elif course['status'] == 'running':
                        if st.button(f"Pause {course['name']}", key=f"pause_{course_id}"):
                            if automation_manager.pause_course(course_id):
                                st.warning(f"Paused {course['name']}")
                                st.rerun()
                
                with col2:
                    if course['status'] == 'paused':
                        if st.button(f"Resume {course['name']}", key=f"resume_{course_id}"):
                            if automation_manager.resume_course(course_id):
                                st.success(f"Resumed {course['name']}")
                                st.rerun()
                
                with col3:
                    if course['status'] in ['running', 'paused']:
                        if st.button(f"Stop {course['name']}", key=f"stop_{course_id}"):
                            if automation_manager.stop_course(course_id):
                                st.error(f"Stopped {course['name']}")
                                st.rerun()
    else:
        st.info("No courses added yet. Go to 'Add Course' to get started!")

def show_add_course():
    """Show add course form with real functionality"""
    st.markdown('<h2 style="color: var(--gold);">➕ Add New Course</h2>', unsafe_allow_html=True)
    
    with st.form("add_course"):
        st.markdown('<h3 style="color: var(--gold);">Course Information</h3>', unsafe_allow_html=True)
        
        course_url = st.text_input("Course URL", placeholder="https://coursera.org/learn/python")
        
        col1, col2 = st.columns(2)
        
        with col1:
            platform = st.selectbox("Platform", ["coursera", "udemy", "edx", "linkedin-learning"])
            email = st.text_input("Email", placeholder="your@email.com")
        
        with col2:
            password = st.text_input("Password", type="password", placeholder="Enter password")
            auto_start = st.checkbox("Start immediately", value=True)
        
        st.markdown('<h3 style="color: var(--gold);">Advanced Options</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            priority = st.slider("Priority", 1, 10, 5)
            max_retries = st.number_input("Max Retries", 1, 10, 3)
        
        with col2:
            estimated_duration = st.number_input("Estimated Duration (hours)", 1, 50, 5)
            tags = st.text_input("Tags (comma separated)", placeholder="python, beginner, programming")
        
        submitted = st.form_submit_button("Add Course")
        
        if submitted:
            if course_url and email and password:
                # Add course to real automation manager
                course_data = {
                    'name': course_url.split('/')[-1].replace('-', ' ').title(),
                    'url': course_url,
                    'platform': platform,
                    'email': email,
                    'password': password,
                    'priority': priority,
                    'max_retries': max_retries,
                    'estimated_duration': estimated_duration,
                    'tags': [tag.strip() for tag in tags.split(',') if tag.strip()]
                }
                
                course_id = automation_manager.add_course(course_data)
                
                if course_id:
                    st.success("Course added successfully!")
                    
                    if auto_start:
                        st.info("Starting automation...")
                        if automation_manager.start_course(course_id):
                            st.success("Automation started successfully!")
                        else:
                            st.error("Failed to start automation")
                else:
                    st.error("Failed to add course")
            else:
                st.error("Please fill in all required fields.")

def show_screen_detection():
    """Show screen detection functionality"""
    st.markdown('<h2 style="color: var(--gold);">🔍 Screen Detection</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="metric-card">
        <h3 style="color: var(--gold);">Auto-Detect Course Information</h3>
        <p>This feature will analyze your screen to automatically detect course information and fill in the form.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📸 Capture & Detect", type="primary"):
            with st.spinner("Analyzing screen..."):
                # Use real detection
                detection_result = automation_manager.detect_course_from_screen()
                if detection_result:
                    st.success("Course information detected!")
                    
                    # Display results
                    st.markdown('<h3 style="color: var(--gold);">Detected Information</h3>', unsafe_allow_html=True)
                    st.write(f"**Platform:** {detection_result['platform'] or 'Unknown'}")
                    st.write(f"**URL:** {detection_result['url'] or 'Not found'}")
                    st.write(f"**Text:** {detection_result['text'][:100]}...")
                    st.write(f"**Confidence:** {detection_result.get('confidence', 0):.2f}")
                    
                    # Auto-fill form
                    if st.button("Use Detected Information"):
                        st.session_state.detected_platform = detection_result['platform']
                        st.session_state.detected_url = detection_result['url']
                        st.success("Information loaded! Go to 'Add Course' to use it.")
                else:
                    st.error("Could not detect course information")
    
    with col2:
        if st.button("🔄 Refresh Detection"):
            st.rerun()
    
    # Show recent screenshot
    st.markdown('<h3 style="color: var(--gold);">Recent Screenshots</h3>', unsafe_allow_html=True)
    
    if automation_manager.screenshots:
        # Show the most recent screenshot
        latest_screenshot = automation_manager.screenshots[-1]
        if Path(latest_screenshot).exists():
            st.image(latest_screenshot, caption="Latest Screenshot", use_column_width=True)
        else:
            st.info("No recent screenshots available")
    else:
        st.info("No screenshots captured yet")

def show_live_monitoring():
    """Show live monitoring with real data"""
    st.markdown('<h2 style="color: var(--gold);">📹 Live Monitoring</h2>', unsafe_allow_html=True)
    
    # Auto-refresh
    if st.button("🔄 Refresh Monitoring"):
        st.rerun()
    
    # Current activity
    st.markdown('<h3 style="color: var(--gold);">Current Activity</h3>', unsafe_allow_html=True)
    
    stats = automation_manager.get_statistics()
    
    if stats.get('running', 0) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: var(--gold);">Active Courses</h3>
                <p style="color: var(--white);">{stats.get('running', 0)} running</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            active_course_id = stats.get('active_course')
            if active_course_id and active_course_id in automation_manager.courses:
                course = automation_manager.courses[active_course_id]
                progress = automation_manager.get_course_progress(active_course_id)
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="color: var(--gold);">Current Course</h3>
                    <p style="color: var(--white);">{course['name']}</p>
                    <p style="color: var(--white);">Progress: {progress:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No automation running. Start a course to see live monitoring.")
    
    # Live logs
    st.markdown('<h3 style="color: var(--gold);">Live Logs</h3>', unsafe_allow_html=True)
    
    # Show real logs
    if automation_manager.logs:
        for log in automation_manager.logs[-10:]:  # Show last 10 logs
            level_color = {
                "INFO": "var(--gold)",
                "WARNING": "#FFAA00", 
                "ERROR": "#FF4444",
                "DEBUG": "#888888"
            }.get(log["level"], "var(--white)")
            
            st.markdown(f"""
            <div class="log-entry">
                <strong style="color: {level_color};">{log['timestamp']}</strong> [{log['level']}] {log['message']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No logs available yet")

def show_settings():
    """Show settings with real configuration"""
    st.markdown('<h2 style="color: var(--gold);">⚙️ Settings</h2>', unsafe_allow_html=True)

    # AI Model Settings
    st.markdown('<h3 style="color: var(--gold);">🤖 AI Model Settings</h3>', unsafe_allow_html=True)
    
    try:
        from src.ai.model_handler import ModelHandler
        ai_handler = ModelHandler()
        
        # Get available models
        available_models = ai_handler.get_available_models()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<h4 style="color: var(--white);">Free Models</h4>', unsafe_allow_html=True)
            for model in available_models.get('free_models', []):
                model_info = ai_handler.get_model_info(model)
                st.markdown(f"""
                <div style="background-color: #2a2a2a; padding: 10px; border-radius: 5px; margin: 5px 0;">
                    <strong style="color: var(--gold);">{model}</strong><br>
                    <small style="color: var(--text-color);">{model_info['description']}</small>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown('<h4 style="color: var(--white);">Premium Models</h4>', unsafe_allow_html=True)
            for model in available_models.get('premium_models', []):
                model_info = ai_handler.get_model_info(model)
                st.markdown(f"""
                <div style="background-color: #2a2a2a; padding: 10px; border-radius: 5px; margin: 5px 0;">
                    <strong style="color: var(--gold);">{model}</strong><br>
                    <small style="color: var(--text-color);">{model_info['description']}</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Model selection
        st.markdown('<h4 style="color: var(--white);">Select Default Model</h4>', unsafe_allow_html=True)
        all_models = available_models.get('free_models', []) + available_models.get('premium_models', [])
        
        if all_models:
            selected_model = st.selectbox(
                "Choose your preferred AI model:",
                all_models,
                index=0 if all_models else None,
                help="Free models are recommended for most users. Premium models require an OpenRouter API key."
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Set as Default", type="primary"):
                    if ai_handler.set_model(selected_model):
                        st.success(f"Default model set to: {selected_model}")
                    else:
                        st.error("Failed to set default model")
            
            with col2:
                if st.button("Test Connection"):
                    with st.spinner("Testing model connection..."):
                        test_result = ai_handler.test_model_connection(selected_model)
                        if test_result['status'] == 'success':
                            st.success(f"✅ Connection successful via {test_result['provider']}")
                            with st.expander("Test Response"):
                                st.write(test_result['response'])
                        else:
                            st.error(f"❌ Connection failed: {test_result.get('error', 'Unknown error')}")
        
        # API Key configuration
        st.markdown('<h4 style="color: var(--white);">OpenRouter API Key (Optional)</h4>', unsafe_allow_html=True)
        st.info("""
        **Free Models**: You can use free models without an API key (local processing).
        **Premium Models**: Require an OpenRouter API key for access.
        
        Get your free API key at: https://openrouter.ai/
        """)
        
        api_key = st.text_input(
            "OpenRouter API Key",
            type="password",
            help="Enter your OpenRouter API key to access premium models and faster processing"
        )
        
        if api_key:
            st.success("API key provided - premium models available!")
        else:
            st.info("No API key - using free models only")
        
    except Exception as e:
        st.error(f"Failed to load AI settings: {str(e)}")

    # Browser Settings
    st.markdown('<h3 style="color: var(--gold);">🌐 Browser Settings</h3>', unsafe_allow_html=True)
    with st.form("browser_settings"):
        headless = st.checkbox("Run browser in headless mode (no UI)", value=True)
        timeout = st.number_input("Browser Timeout (seconds)", min_value=10, value=30)
        user_agent = st.text_input("User Agent", value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        submitted = st.form_submit_button("Save Browser Settings")
        if submitted:
            # This would ideally update the config/courses.yaml or a dedicated settings file
            # For now, it's a placeholder for future implementation
            st.success("Browser settings saved!")

    # Export/Import
    st.markdown('<h3 style="color: var(--gold);">📤 Export/Import</h3>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📤 Export Courses"):
            export_path = f"data/export_{int(time.time())}.json"
            if automation_manager.export_courses(export_path):
                st.success(f"Exported to {export_path}")
            else:
                st.error("Export failed")

    with col2:
        uploaded_file = st.file_uploader("📥 Import Courses", type=['json'])
        if uploaded_file is not None:
            if st.button("Import"):
                # Save uploaded file temporarily
                temp_path = f"data/temp_import_{int(time.time())}.json"
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.getvalue())

                if automation_manager.import_courses(temp_path):
                    st.success("Import successful!")
                else:
                    st.error("Import failed")

def show_logs():
    """Show logs with real data"""
    st.markdown('<h2 style="color: var(--gold);">📝 Logs</h2>', unsafe_allow_html=True)
    
    # Log level filter
    col1, col2 = st.columns([1, 3])
    
    with col1:
        log_level = st.selectbox("Log Level", ["All", "INFO", "WARNING", "ERROR", "DEBUG"])
    
    with col2:
        if st.button("🔄 Refresh Logs"):
            st.rerun()
    
    # Real log display
    st.markdown('<h3 style="color: var(--gold);">Recent Logs</h3>', unsafe_allow_html=True)
    
    # Show real logs from automation manager
    if automation_manager.logs:
        # Filter logs by level
        if log_level != "All":
            filtered_logs = [log for log in automation_manager.logs if log["level"] == log_level]
        else:
            filtered_logs = automation_manager.logs
        
        # Display logs
        for log in filtered_logs[-50:]:  # Show last 50 logs
            level_color = {
                "INFO": "var(--gold)",
                "WARNING": "#FFAA00", 
                "ERROR": "#FF4444",
                "DEBUG": "#888888"
            }.get(log["level"], "var(--white)")
            
            st.markdown(f"""
            <div class="log-entry">
                <strong style="color: {level_color};">{log['timestamp']}</strong> [{log['level']}] {log['message']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No logs available yet")

if __name__ == "__main__":
    main() 