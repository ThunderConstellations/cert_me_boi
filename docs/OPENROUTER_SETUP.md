# 🔑 OpenRouter API Setup Guide

This guide will help you set up your OpenRouter API key for use with DeepSeek R1 Free model in both the Cert Me Boi application and Cursor IDE.

## 📋 Prerequisites

- OpenRouter account (free at [openrouter.ai](https://openrouter.ai))
- Cursor IDE installed
- Python environment for Cert Me Boi

## 🚀 Step 1: Get Your OpenRouter API Key

1. **Create an OpenRouter Account**

   - Visit [openrouter.ai](https://openrouter.ai)
   - Sign up with your email or GitHub account

2. **Generate API Key**
   - Navigate to [API Keys](https://openrouter.ai/keys)
   - Click "Create Key"
   - Give it a descriptive name like "Cert Me Boi - DeepSeek"
   - Copy the generated API key (starts with `sk-or-v1-...`)

## 🛠️ Step 2: Configure Cert Me Boi

1. **Create Environment File**

   ```bash
   # In your cert_me_boi root directory
   cp config/openrouter.env.template .env
   ```

2. **Edit the .env file**

   ```bash
   # Replace 'your_openrouter_api_key_here' with your actual API key
   OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
   DEFAULT_AI_MODEL=openrouter/deepseek/deepseek-r1-free
   BACKUP_AI_MODEL=openrouter/deepseek/deepseek-chat
   ```

3. **Test Configuration**
   ```bash
   python -c "from src.ai.model_handler import ModelHandler; print('✅ OpenRouter configured successfully!')"
   ```

## 🎯 Step 3: Configure Cursor IDE

### Method 1: Using Cursor Settings (Recommended)

1. **Open Cursor Settings**

   - Press `Ctrl+,` (Windows/Linux) or `Cmd+,` (Mac)
   - Search for "AI" or "Language Model"

2. **Configure Custom Model**

   - Find "AI Model Provider" settings
   - Select "Custom" or "OpenRouter"
   - Add the following configuration:

   ```json
   {
     "ai.model": "openrouter/deepseek/deepseek-r1-free",
     "ai.apiKey": "sk-or-v1-your-actual-key-here",
     "ai.baseURL": "https://openrouter.ai/api/v1",
     "ai.provider": "openrouter"
   }
   ```

### Method 2: Environment Variables

1. **Set System Environment Variables** (Windows)

   ```powershell
   # Open PowerShell as Administrator
   [Environment]::SetEnvironmentVariable("OPENROUTER_API_KEY", "sk-or-v1-your-actual-key-here", "User")
   [Environment]::SetEnvironmentVariable("CURSOR_AI_MODEL", "openrouter/deepseek/deepseek-r1-free", "User")
   ```

2. **Set Environment Variables** (Linux/Mac)

   ```bash
   # Add to your ~/.bashrc or ~/.zshrc
   export OPENROUTER_API_KEY="sk-or-v1-your-actual-key-here"
   export CURSOR_AI_MODEL="openrouter/deepseek/deepseek-r1-free"

   # Reload your shell
   source ~/.bashrc
   ```

### Method 3: Cursor Workspace Settings

1. **Create .cursor-settings.json**
   ```json
   {
     "ai.model": "openrouter/deepseek/deepseek-r1-free",
     "ai.apiKey": "sk-or-v1-your-actual-key-here",
     "ai.baseURL": "https://openrouter.ai/api/v1",
     "ai.maxTokens": 4096,
     "ai.temperature": 0.1
   }
   ```

## 🔍 Step 4: Verify Setup

### Test in Cert Me Boi

```bash
python cli.py demo --model "openrouter/deepseek/deepseek-r1-free"
```

### Test in Cursor

1. Open any file in your project
2. Press `Ctrl+K` to open the AI chat
3. Type a simple question like "Explain this code"
4. Verify you see "DeepSeek" responses

## 💡 DeepSeek R1 Free Model Details

- **Model ID**: `openrouter/deepseek/deepseek-r1-free`
- **Context Length**: 32,768 tokens
- **Cost**: Free (with rate limits)
- **Best For**: Code generation, explanation, debugging
- **Rate Limits**: ~10 requests/minute for free tier

## 🎯 Advanced Configuration

### Custom Model Parameters

```json
{
  "model": "openrouter/deepseek/deepseek-r1-free",
  "temperature": 0.1,
  "max_tokens": 4096,
  "top_p": 0.9,
  "frequency_penalty": 0.1,
  "presence_penalty": 0.1
}
```

### Fallback Models

If DeepSeek R1 Free is unavailable:

1. `openrouter/deepseek/deepseek-chat` (backup)
2. `openrouter/meta-llama/llama-3.1-8b-instruct:free`
3. `openrouter/google/gemma-2-9b-it:free`

## ❗ Troubleshooting

### Common Issues

1. **"API Key Invalid" Error**

   - Verify your API key starts with `sk-or-v1-`
   - Check for extra spaces or characters
   - Regenerate key if needed

2. **"Model Not Found" Error**

   - Ensure model ID is exactly: `openrouter/deepseek/deepseek-r1-free`
   - Check OpenRouter's model availability

3. **Rate Limit Exceeded**

   - Wait 1 minute between requests
   - Consider upgrading to paid tier
   - Use backup models

4. **Cursor Not Using Custom Model**
   - Restart Cursor IDE
   - Check workspace settings override global settings
   - Verify API key is set correctly

### Getting Help

- **OpenRouter Support**: [support@openrouter.ai](mailto:support@openrouter.ai)
- **Cursor Documentation**: [cursor.sh/docs](https://cursor.sh/docs)
- **Project Issues**: [GitHub Issues](https://github.com/ThunderConstellations/cert_me_boi/issues)

## 🔒 Security Notes

- Never commit API keys to version control
- Use environment variables or secure storage
- Rotate keys periodically
- Monitor usage on OpenRouter dashboard

---

**🎉 You're all set!** Your OpenRouter DeepSeek R1 Free model should now work with both Cert Me Boi and Cursor IDE.
