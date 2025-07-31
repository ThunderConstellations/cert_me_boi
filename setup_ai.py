#!/usr/bin/env python3
"""
AI Setup Script for Cert Me Boi
Helps users configure AI models and OpenRouter API key
"""

import os
import sys
import yaml
from pathlib import Path

def setup_ai_configuration():
    """Interactive setup for AI configuration"""
    print("🎓 Cert Me Boi - AI Configuration Setup")
    print("=" * 50)
    
    # Check if config file exists
    config_path = Path("config/courses.yaml")
    if not config_path.exists():
        print("❌ Configuration file not found. Please run the main setup first.")
        return False
    
    # Load current config
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False
    
    print("\n🤖 AI Model Configuration")
    print("-" * 30)
    
    # Show available models
    ai_config = config.get('ai', {})
    free_models = ai_config.get('model_categories', {}).get('free_models', [])
    premium_models = ai_config.get('model_categories', {}).get('premium_models', [])
    
    print("\n📋 Available Free Models:")
    for i, model in enumerate(free_models, 1):
        print(f"  {i}. {model}")
    
    print("\n💎 Available Premium Models (require API key):")
    for i, model in enumerate(premium_models, 1):
        print(f"  {i}. {model}")
    
    # Model selection
    print("\n🔧 Model Selection:")
    print("1. Use free models (recommended for beginners)")
    print("2. Use premium models (requires OpenRouter API key)")
    print("3. Skip AI configuration")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        # Free models
        print("\n✅ Free models selected!")
        print("You can use the system without any API key.")
        config['ai']['default_provider'] = 'local'
        config['ai']['default_model'] = free_models[0] if free_models else "microsoft/phi-2"
        
    elif choice == "2":
        # Premium models
        print("\n💎 Premium models selected!")
        print("\nTo use premium models, you need an OpenRouter API key.")
        print("1. Go to https://openrouter.ai/")
        print("2. Sign up for a free account")
        print("3. Get your API key from the dashboard")
        
        api_key = input("\nEnter your OpenRouter API key (or press Enter to skip): ").strip()
        
        if api_key:
            config['ai']['api_key'] = api_key
            config['ai']['default_provider'] = 'openrouter'
            config['ai']['default_model'] = premium_models[0] if premium_models else free_models[0]
            print("✅ API key configured!")
        else:
            print("⚠️  No API key provided. Using free models instead.")
            config['ai']['default_provider'] = 'local'
            config['ai']['default_model'] = free_models[0] if free_models else "microsoft/phi-2"
    
    elif choice == "3":
        print("⏭️  Skipping AI configuration.")
        return True
    
    else:
        print("❌ Invalid choice. Using default configuration.")
        return False
    
    # Save configuration
    try:
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        print("\n✅ Configuration saved successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to save configuration: {e}")
        return False

def test_ai_connection():
    """Test the AI connection"""
    print("\n🧪 Testing AI Connection")
    print("-" * 30)
    
    try:
        from src.ai.model_handler import ModelHandler
        
        handler = ModelHandler()
        test_result = handler.test_model_connection()
        
        if test_result['status'] == 'success':
            print(f"✅ Connection successful!")
            print(f"   Model: {test_result['model']}")
            print(f"   Provider: {test_result['provider']}")
            print(f"   Response: {test_result['response'][:100]}...")
        else:
            print(f"❌ Connection failed: {test_result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test connection: {e}")
        return False
    
    return True

def main():
    """Main setup function"""
    print("🚀 Welcome to Cert Me Boi AI Setup!")
    
    # Setup AI configuration
    if setup_ai_configuration():
        print("\n🎉 Setup completed successfully!")
        
        # Test connection
        test_choice = input("\nWould you like to test the AI connection? (y/n): ").strip().lower()
        if test_choice in ['y', 'yes']:
            test_ai_connection()
    else:
        print("\n❌ Setup failed. Please check your configuration.")
        return 1
    
    print("\n📚 Next Steps:")
    print("1. Run 'python run_gui.py' to start the GUI")
    print("2. Go to Settings > AI Model Settings to customize further")
    print("3. Add your first course and start automating!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 