# userinput.py
import os
from datetime import datetime

# Ensure tmp directory exists
os.makedirs("tmp", exist_ok=True)

LAST_PROMPT_FILE = "tmp/last_prompt.txt"
PROMPT_HISTORY_FILE = "tmp/prompt_history.txt"

def load_last_prompt():
    """Load the last prompt from storage"""
    if os.path.exists(LAST_PROMPT_FILE):
        with open(LAST_PROMPT_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return "continue with previous task context and improve the codebase"

def save_prompt(prompt):
    """Save prompt to storage and history"""
    # Save as last prompt
    with open(LAST_PROMPT_FILE, 'w', encoding='utf-8') as f:
        f.write(prompt)
    
    # Append to history with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(PROMPT_HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {prompt}\n")

def get_automated_prompt():
    """Get prompt automatically - always use last stored prompt for automation"""
    last_prompt = load_last_prompt()
    print(f"prompt: (auto-continuing with: {last_prompt})")
    return last_prompt

# Main execution
if __name__ == "__main__":
    # Get prompt (fully automated)
    user_input = get_automated_prompt()
    
    # Save the prompt for next iteration
    save_prompt(user_input)
    
    # Output the prompt for the AI to process
    print(user_input)
