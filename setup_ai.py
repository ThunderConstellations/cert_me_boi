#!/usr/bin/env python3
"""
Interactive AI model setup for Cert Me Boi
Helps configure OpenRouter API keys and select AI models
"""

import os
import sys
import yaml
from pathlib import Path

def get_user_input(prompt, default=None):
    """Get user input with optional default value"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()

def setup_openrouter_api():
    """Set up OpenRouter API key and configuration"""
    print("\n🤖 OpenRouter API Setup")
    print("=" * 50)
    print("OpenRouter provides access to many AI models including free DeepSeek models.")
    print("Visit https://openrouter.ai to create an account and get your API key.")
    print()
    
    # Get API key
    api_key = get_user_input("Enter your OpenRouter API key (optional for some free models)")
    
    if not api_key:
        print("\n⚠️  No API key provided. You can still use local models.")
        print("Some free models on OpenRouter don't require an API key.")
        return None
    
    # Validate API key format
    if not api_key.startswith('sk-or-v1-'):
        print("\n⚠️  Warning: OpenRouter API keys typically start with 'sk-or-v1-'")
        confirm = get_user_input("Continue anyway? (y/n)", "n")
        if confirm.lower() != 'y':
            return None
    
    return api_key

def setup_model_preferences():
    """Set up model preferences"""
    print("\n🎯 Model Selection")
    print("=" * 50)
    
    # Free models (recommended) - Updated with DeepSeek R1
    free_models = [
        "deepseek/deepseek-r1-0528:free",  # NEW: Best free model - o1 performance level
        "deepseek-ai/deepseek-coder-6.7b-instruct",
        "deepseek-ai/deepseek-llm-7b-chat", 
        "deepseek-ai/deepseek-math-7b-instruct",
        "microsoft/phi-2",
        "microsoft/phi-3-mini-4k-instruct"
    ]
    
    # Premium models
    premium_models = [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4",
        "google/gemini-pro-1.5",
        "meta-llama/llama-3.1-8b-instruct"
    ]
    
    print("Available Free Models:")
    for i, model in enumerate(free_models, 1):
        if i == 1:
            print(f"  {i}. {model} ⭐ RECOMMENDED - o1 performance level!")
        else:
            print(f"  {i}. {model}")
    
    print("\nAvailable Premium Models:")
    for i, model in enumerate(premium_models, 1):
        print(f"  {i + len(free_models)}. {model}")
    
    print(f"\n💡 Recommended: DeepSeek R1 0528 (option 1) - FREE model with o1-level performance!")
    print("   This model has 671B parameters and performs on par with OpenAI's o1 model.")
    
    choice = get_user_input(f"Select default model (1-{len(free_models + premium_models)})", "1")
    
    try:
        choice_idx = int(choice) - 1
        all_models = free_models + premium_models
        if 0 <= choice_idx < len(all_models):
            selected_model = all_models[choice_idx]
            is_free = choice_idx < len(free_models)
            return selected_model, is_free
        else:
            print("Invalid choice, using default DeepSeek R1")
            return free_models[0], True
    except ValueError:
        print("Invalid input, using default DeepSeek R1")
        return free_models[0], True

def update_config_file(api_key, selected_model, is_free):
    """Update the courses.yaml configuration file"""
    config_path = Path("config/courses.yaml")
    
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    try:
        # Read existing config
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Update AI section
        if 'ai' not in config:
            config['ai'] = {}
        
        # Set API key (if provided)
        if api_key:
            config['ai']['api_key'] = api_key
        
        # Set default model
        config['ai']['default_model'] = selected_model
        
        # Update model categories with DeepSeek R1
        config['ai']['model_categories'] = {
            'free_models': [
                "deepseek/deepseek-r1-0528:free",  # NEW: Best free model
                "deepseek-ai/deepseek-coder-6.7b-instruct",
                "deepseek-ai/deepseek-llm-7b-chat",
                "deepseek-ai/deepseek-math-7b-instruct",
                "microsoft/phi-2",
                "microsoft/phi-3-mini-4k-instruct"
            ],
            'premium_models': [
                "anthropic/claude-3.5-sonnet",
                "openai/gpt-4",
                "google/gemini-pro-1.5",
                "meta-llama/llama-3.1-8b-instruct"
            ]
        }
        
        # Update OpenRouter models list
        config['ai']['openrouter_models'] = [
            "deepseek/deepseek-r1-0528:free",
            "deepseek-ai/deepseek-coder-6.7b-instruct",
            "deepseek-ai/deepseek-llm-7b-chat",
            "deepseek-ai/deepseek-math-7b-instruct",
            "microsoft/phi-2",
            "microsoft/phi-3-mini-4k-instruct"
        ]
        
        # Update other AI settings
        config['ai'].update({
            'temperature': 0.7,
            'max_tokens': 1000,  # Increased for R1 model
            'use_openrouter': True,
            'fallback_to_local': True
        })
        
        # Write updated config
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Configuration updated successfully!")
        print(f"   Default model: {selected_model}")
        print(f"   Model type: {'Free' if is_free else 'Premium'}")
        if selected_model == "deepseek/deepseek-r1-0528:free":
            print("   🚀 You're using the latest DeepSeek R1 model with o1-level performance!")
        if api_key:
            print(f"   API key: {'*' * (len(api_key) - 8) + api_key[-8:]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        return False

def setup_environment_variables(api_key):
    """Set up environment variables for API key"""
    if not api_key:
        return
    
    print("\n🔧 Environment Setup")
    print("=" * 50)
    
    # Create .env file
    env_path = Path(".env")
    env_content = f"OPENROUTER_API_KEY={api_key}\n"
    
    if env_path.exists():
        # Read existing .env
        with open(env_path, 'r') as f:
            existing_content = f.read()
        
        # Update or add the API key
        lines = existing_content.split('\n')
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('OPENROUTER_API_KEY='):
                lines[i] = f"OPENROUTER_API_KEY={api_key}"
                updated = True
                break
        
        if not updated:
            lines.append(f"OPENROUTER_API_KEY={api_key}")
        
        env_content = '\n'.join(lines)
    
    # Write .env file
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Environment file created: {env_path}")
    print("   You can also set this as a system environment variable.")

def test_configuration():
    """Test the AI configuration"""
    print("\n🧪 Testing Configuration")
    print("=" * 50)
    
    try:
        # Add src to path for imports
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        from src.ai.model_handler import ModelHandler
        
        # Initialize model handler
        model_handler = ModelHandler()
        
        # Test model loading
        print("Loading AI model...")
        success = model_handler.load_model()
        
        if success:
            print("✅ AI model loaded successfully!")
            
            # Test text generation
            print("Testing text generation...")
            response = model_handler.generate_text("Hello! Can you help me with course automation?")
            
            if response:
                print("✅ AI model is working correctly!")
                print(f"   Sample response: {response[:100]}...")
            else:
                print("⚠️  AI model loaded but text generation failed")
        else:
            print("❌ Failed to load AI model")
            
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        print("   You can still use the application, but AI features may not work.")

def main():
    """Main setup function"""
    print("🎓 Cert Me Boi - AI Setup")
    print("=" * 50)
    print("This script will help you configure AI models for course automation.")
    print()
    
    # Setup API key
    api_key = setup_openrouter_api()
    
    # Setup model preferences
    selected_model, is_free = setup_model_preferences()
    
    # Update configuration
    config_updated = update_config_file(api_key, selected_model, is_free)
    
    if not config_updated:
        print("❌ Setup failed. Please check the configuration manually.")
        return
    
    # Setup environment variables
    setup_environment_variables(api_key)
    
    # Test configuration
    print(f"\n🎉 Setup Complete!")
    print("=" * 50)
    print("Your AI configuration is ready!")
    print()
    print("Next steps:")
    print("1. Run 'python cli.py gui' to start the web interface")
    print("2. Or run 'python cli.py demo' to test the automation")
    print("3. Check the GUI settings to verify your model selection")
    print()
    
    test_choice = get_user_input("Test the configuration now? (y/n)", "y")
    if test_choice.lower() == 'y':
        test_configuration()

if __name__ == "__main__":
    main() 