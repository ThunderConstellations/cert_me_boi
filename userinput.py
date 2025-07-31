# userinput.py
"""Module for capturing user input."""

def get_user_input(prompt_message="Enter your input: "):
    """
    Get input from the user with a customizable prompt.
    
    Args:
        prompt_message (str): The message to display to the user
        
    Returns:
        str: The user's input, or None if cancelled
    """
    try:
        return input(prompt_message)
    except (KeyboardInterrupt, EOFError):
        print("\nInput cancelled by user.")
        return None

if __name__ == "__main__":
    user_input = get_user_input("Please enter your input: ")
    if user_input is not None:
        print(f"You entered: {user_input}")