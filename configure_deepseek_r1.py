#!/usr/bin/env python3
"""
Automatically configure DeepSeek R1 as the default AI model
"""

import yaml
from pathlib import Path

def configure_deepseek_r1():
    """Configure DeepSeek R1 as the default model"""
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
        
        # Set DeepSeek R1 as default model
        config['ai']['default_model'] = "deepseek/deepseek-r1-0528:free"
        config['ai']['default_provider'] = "openrouter"
        
        # Update model categories with DeepSeek R1 first
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
            'fallback_to_local': True,
            'api_key': ""  # User can add their API key later if needed
        })
        
        # Write updated config
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        print("✅ DeepSeek R1 configured successfully!")
        print("   🚀 Default model: deepseek/deepseek-r1-0528:free")
        print("   🔧 Max tokens: 1000 (optimized for R1)")
        print("   🌐 Provider: OpenRouter")
        print("   📋 Free model with o1-level performance!")
        print()
        print("ℹ️  Note: You can optionally add an OpenRouter API key to config/courses.yaml")
        print("   for better rate limits, but the model should work without one.")
        print()
        print("Next steps:")
        print("1. Run 'python cli.py gui' to start the web interface")
        print("2. Or run 'python cli.py demo' to test the automation")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        return False

if __name__ == "__main__":
    print("🤖 Configuring DeepSeek R1 Model...")
    print("=" * 50)
    configure_deepseek_r1() 