"""
Cert Me Boi - Streamlit GUI Application
A modern web interface for the automated course certification system.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import yaml
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.main import CertificationAutomation
from src.utils.logger import logger
from src.utils.metrics_collector import MetricsCollector

# Page configuration
st.set_page_config(
    page_title="Cert Me Boi - Course Automation",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
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
    }
    .status-running {
        color: #28a745;
        font-weight: bold;
    }
    .status-stopped {
        color: #dc3545;
        font-weight: bold;
    }
    .status-paused {
        color: #ffc107;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class CertMeBoiGUI:
    def __init__(self):
        self.automation = None
        self.metrics = MetricsCollector()
        self.load_config()
        
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            config_path = Path("config/courses.yaml")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
            else:
                self.config = {}
        except Exception as e:
            st.error(f"Failed to load configuration: {e}")
            self.config = {}
    
    def save_config(self):
        """Save configuration to YAML file"""
        try:
            config_path = Path("config/courses.yaml")
            config_path.parent.mkdir(exist_ok=True)
            with open(config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            st.success("Configuration saved successfully!")
        except Exception as e:
            st.error(f"Failed to save configuration: {e}")
    
    def get_automation_status(self):
        """Get current automation status"""
        if self.automation is None:
            return "stopped"
        # This would need to be implemented based on the actual automation state
        return "running"  # Placeholder
    
    def start_automation(self, course_url, email, password):
        """Start course automation"""
        try:
            with st.spinner("Starting automation..."):
                self.automation = CertificationAutomation()
                # Start automation in a separate thread
                thread = threading.Thread(
                    target=self.automation.start_automation,
                    args=(course_url, email, password)
                )
                thread.daemon = True
                thread.start()
                st.success("Automation started successfully!")
                return True
        except Exception as e:
            st.error(f"Failed to start automation: {e}")
            return False
    
    def stop_automation(self):
        """Stop course automation"""
        try:
            if self.automation:
                self.automation.cleanup()
                self.automation = None
                st.success("Automation stopped successfully!")
                return True
        except Exception as e:
            st.error(f"Failed to stop automation: {e}")
            return False
    
    def get_metrics_data(self):
        """Get metrics data for visualization"""
        # Sample data - replace with actual metrics
        return {
            'success_rate': 94.2,
            'avg_completion_time': 2.3,
            'certificates_earned': 12,
            'active_courses': 2,
            'total_courses': 15
        }
    
    def create_progress_chart(self):
        """Create progress visualization chart"""
        # Sample data - replace with actual course progress
        courses = ['Python Basics', 'Data Science', 'Machine Learning', 'Web Development']
        progress = [75, 45, 30, 90]
        
        fig = px.bar(
            x=courses,
            y=progress,
            title="Course Progress",
            labels={'x': 'Course', 'y': 'Progress (%)'},
            color=progress,
            color_continuous_scale='viridis'
        )
        fig.update_layout(height=400)
        return fig
    
    def create_performance_chart(self):
        """Create performance metrics chart"""
        # Sample data - replace with actual performance data
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        completion_times = [2.1, 2.3, 1.9, 2.5, 2.0, 2.2, 2.4, 1.8, 2.1, 2.3] * 3 + [2.0]
        
        fig = px.line(
            x=dates,
            y=completion_times,
            title="Average Completion Time (Hours)",
            labels={'x': 'Date', 'y': 'Hours'},
            markers=True
        )
        fig.update_layout(height=300)
        return fig

def main():
    """Main Streamlit application"""
    gui = CertMeBoiGUI()
    
    # Sidebar navigation
    st.sidebar.title("🎓 Cert Me Boi")
    page = st.sidebar.selectbox(
        "Navigation",
        ["Dashboard", "Course Management", "Settings", "Logs", "Analytics"]
    )
    
    # Main content area
    if page == "Dashboard":
        show_dashboard(gui)
    elif page == "Course Management":
        show_course_management(gui)
    elif page == "Settings":
        show_settings(gui)
    elif page == "Logs":
        show_logs(gui)
    elif page == "Analytics":
        show_analytics(gui)

def show_dashboard(gui):
    """Show main dashboard"""
    st.markdown('<h1 class="main-header">🎓 Cert Me Boi Dashboard</h1>', unsafe_allow_html=True)
    
    # Status and quick actions
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        status = gui.get_automation_status()
        status_class = f"status-{status}"
        st.markdown(f'<p class="{status_class}">Status: {status.upper()}</p>', unsafe_allow_html=True)
    
    with col2:
        if st.button("🚀 Start Automation", type="primary"):
            gui.start_automation("https://example.com", "test@example.com", "password")
    
    with col3:
        if st.button("⏹️ Stop Automation"):
            gui.stop_automation()
    
    # Metrics cards
    st.subheader("📊 Performance Metrics")
    metrics = gui.get_metrics_data()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Success Rate</h3>
            <h2>{metrics['success_rate']}%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Avg. Completion</h3>
            <h2>{metrics['avg_completion_time']}h</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Certificates</h3>
            <h2>{metrics['certificates_earned']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Active Courses</h3>
            <h2>{metrics['active_courses']}/{metrics['total_courses']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(gui.create_progress_chart(), use_container_width=True)
    
    with col2:
        st.plotly_chart(gui.create_performance_chart(), use_container_width=True)
    
    # Recent activity
    st.subheader("📝 Recent Activity")
    activity_data = [
        {"Time": "2 min ago", "Action": "Completed Python Basics", "Status": "✅"},
        {"Time": "15 min ago", "Action": "Started Data Science course", "Status": "🔄"},
        {"Time": "1 hour ago", "Action": "Downloaded certificate", "Status": "📄"},
        {"Time": "2 hours ago", "Action": "Solved quiz questions", "Status": "🧠"}
    ]
    
    activity_df = pd.DataFrame(activity_data)
    st.dataframe(activity_df, use_container_width=True, hide_index=True)

def show_course_management(gui):
    """Show course management interface"""
    st.title("📚 Course Management")
    
    # Add new course
    st.subheader("➕ Add New Course")
    
    with st.form("add_course"):
        col1, col2 = st.columns(2)
        
        with col1:
            course_url = st.text_input("Course URL")
            platform = st.selectbox("Platform", ["Coursera", "Udemy", "edX", "LinkedIn Learning"])
        
        with col2:
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
        
        submitted = st.form_submit_button("Add Course")
        if submitted:
            if course_url and email and password:
                st.success("Course added successfully!")
            else:
                st.error("Please fill in all required fields.")
    
    # Course list
    st.subheader("📋 Active Courses")
    
    # Sample course data
    courses = [
        {"Name": "Python Basics", "Platform": "Coursera", "Progress": 75, "Status": "Running"},
        {"Name": "Data Science", "Platform": "Udemy", "Progress": 45, "Status": "Paused"},
        {"Name": "Machine Learning", "Platform": "edX", "Progress": 30, "Status": "Stopped"}
    ]
    
    for course in courses:
        with st.expander(f"{course['Name']} ({course['Platform']})"):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.progress(course['Progress'] / 100)
                st.write(f"Progress: {course['Progress']}%")
            
            with col2:
                st.write(f"Status: {course['Status']}")
            
            with col3:
                if st.button("Resume", key=f"resume_{course['Name']}"):
                    st.success(f"Resumed {course['Name']}")
            
            with col4:
                if st.button("Stop", key=f"stop_{course['Name']}"):
                    st.success(f"Stopped {course['Name']}")

def show_settings(gui):
    """Show settings interface"""
    st.title("⚙️ Settings")
    
    # AI Configuration
    st.subheader("🤖 AI Configuration")
    
    with st.form("ai_settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            default_model = st.selectbox(
                "Default AI Model",
                ["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet", "local-model"]
            )
            openrouter_key = st.text_input("OpenRouter API Key", type="password")
        
        with col2:
            confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.8)
            max_retries = st.number_input("Max Retries", 1, 10, 3)
        
        submitted = st.form_submit_button("Save AI Settings")
        if submitted:
            st.success("AI settings saved!")
    
    # Browser Configuration
    st.subheader("🌐 Browser Configuration")
    
    with st.form("browser_settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            headless = st.checkbox("Headless Mode", value=True)
            timeout = st.number_input("Timeout (seconds)", 10, 120, 30)
        
        with col2:
            user_agent = st.text_input("User Agent", value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            viewport_width = st.number_input("Viewport Width", 800, 1920, 1366)
        
        submitted = st.form_submit_button("Save Browser Settings")
        if submitted:
            st.success("Browser settings saved!")
    
    # Monitoring Configuration
    st.subheader("📹 Monitoring Configuration")
    
    with st.form("monitor_settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            capture_interval = st.number_input("Capture Interval (ms)", 100, 5000, 1000)
            screenshot_quality = st.slider("Screenshot Quality", 50, 100, 80)
        
        with col2:
            enable_ocr = st.checkbox("Enable OCR", value=True)
            enable_motion_detection = st.checkbox("Enable Motion Detection", value=True)
        
        submitted = st.form_submit_button("Save Monitor Settings")
        if submitted:
            st.success("Monitor settings saved!")

def show_logs(gui):
    """Show logs interface"""
    st.title("📝 Logs")
    
    # Log level filter
    col1, col2 = st.columns([1, 3])
    
    with col1:
        log_level = st.selectbox("Log Level", ["All", "INFO", "WARNING", "ERROR", "DEBUG"])
    
    with col2:
        if st.button("🔄 Refresh Logs"):
            st.rerun()
    
    # Log display
    st.subheader("Recent Logs")
    
    # Sample log data - replace with actual log reading
    logs = [
        {"Timestamp": "2024-01-15 14:30:25", "Level": "INFO", "Message": "Automation started successfully"},
        {"Timestamp": "2024-01-15 14:30:26", "Level": "INFO", "Message": "Logged into Coursera"},
        {"Timestamp": "2024-01-15 14:30:27", "Level": "WARNING", "Message": "Slow page load detected"},
        {"Timestamp": "2024-01-15 14:30:28", "Level": "INFO", "Message": "Video progress: 45%"},
        {"Timestamp": "2024-01-15 14:30:29", "Level": "ERROR", "Message": "Failed to click element"}
    ]
    
    # Filter logs by level
    if log_level != "All":
        logs = [log for log in logs if log["Level"] == log_level]
    
    # Display logs
    for log in logs:
        level_color = {
            "INFO": "blue",
            "WARNING": "orange", 
            "ERROR": "red",
            "DEBUG": "gray"
        }.get(log["Level"], "black")
        
        st.markdown(f"""
        <div style="border-left: 3px solid {level_color}; padding-left: 10px; margin: 5px 0;">
            <strong>{log['Timestamp']}</strong> [{log['Level']}] {log['Message']}
        </div>
        """, unsafe_allow_html=True)

def show_analytics(gui):
    """Show analytics interface"""
    st.title("📈 Analytics")
    
    # Time period selector
    col1, col2 = st.columns([1, 3])
    
    with col1:
        time_period = st.selectbox("Time Period", ["Last 7 days", "Last 30 days", "Last 3 months", "All time"])
    
    with col2:
        if st.button("🔄 Refresh Analytics"):
            st.rerun()
    
    # Performance metrics
    st.subheader("Performance Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Success rate over time
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        success_rates = [92, 94, 91, 95, 93, 96, 94, 92, 95, 93] * 3 + [94]
        
        fig = px.line(
            x=dates,
            y=success_rates,
            title="Success Rate Over Time",
            labels={'x': 'Date', 'y': 'Success Rate (%)'},
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Course completion distribution
        platforms = ['Coursera', 'Udemy', 'edX', 'LinkedIn Learning']
        completions = [45, 30, 15, 10]
        
        fig = px.pie(
            values=completions,
            names=platforms,
            title="Completions by Platform"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed statistics
    st.subheader("Detailed Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Courses Started", "156")
        st.metric("Average Completion Time", "2.3 hours")
        st.metric("Best Performing Platform", "Coursera")
    
    with col2:
        st.metric("Success Rate", "94.2%")
        st.metric("Average Score", "87.5%")
        st.metric("Most Popular Course", "Python Basics")
    
    with col3:
        st.metric("Total Certificates", "142")
        st.metric("Failed Attempts", "9")
        st.metric("Total Study Time", "358 hours")

if __name__ == "__main__":
    main() 