import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import requests
import json
import yaml
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from src.utils.logger import ai_logger, log_ai_interaction, log_error_with_context, logger, log_execution_time

class ModelHandler:
    # Model metadata dictionary for robust model identification
    MODEL_METADATA = {
        # Free models
        "deepseek-ai/deepseek-coder-6.7b-instruct": {
            "provider": "openrouter",
            "is_free": True,
            "description": "Free Deepseek model for coding and general tasks",
            "recommended_for": ["coding", "text generation", "question answering"]
        },
        "deepseek-ai/deepseek-coder-33b-instruct": {
            "provider": "openrouter",
            "is_free": True,
            "description": "Free Deepseek model for advanced coding tasks",
            "recommended_for": ["coding", "complex programming", "code review"]
        },
        "microsoft/phi-2": {
            "provider": "local",
            "is_free": True,
            "description": "Free Microsoft Phi model for general tasks",
            "recommended_for": ["text generation", "summarization", "general AI tasks"]
        },
        "microsoft/phi-3-mini": {
            "provider": "local",
            "is_free": True,
            "description": "Free Microsoft Phi-3 Mini model for efficient text generation",
            "recommended_for": ["text generation", "summarization", "lightweight tasks"]
        },
        # Premium models
        "openai/gpt-4": {
            "provider": "openrouter",
            "is_free": False,
            "description": "Premium GPT-4 model with advanced capabilities",
            "recommended_for": ["complex tasks", "high-quality output", "creative writing"]
        },
        "anthropic/claude-3-opus": {
            "provider": "openrouter",
            "is_free": False,
            "description": "Premium Claude-3 Opus model for advanced reasoning",
            "recommended_for": ["complex reasoning", "analysis", "research"]
        },
        "anthropic/claude-3-sonnet": {
            "provider": "openrouter",
            "is_free": False,
            "description": "Premium Claude-3 Sonnet model for balanced performance",
            "recommended_for": ["general tasks", "analysis", "content creation"]
        }
    }

    def __init__(self, config_path: str = "config/courses.yaml"):
        """Initialize the model handler with configuration"""
        self.config = self._load_config(config_path)
        self.ai_config = self.config['ai']
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Model handler initialized on {self.device}", module="ai")

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}", module="ai")
            raise

    @log_execution_time
    def load_model(self, model_name: Optional[str] = None) -> bool:
        """Load the specified model or default model with fallback to OpenRouter"""
        try:
            model_name = model_name or self.ai_config['default_model']
            provider = self.ai_config.get('default_provider', 'openrouter')

            # Try OpenRouter first if configured
            if provider == 'openrouter' and self.ai_config.get('api_key'):
                logger.info(f"Using OpenRouter with model: {model_name}", module="ai")
                return True  # OpenRouter models are loaded on-demand

            # Fallback to local model
            logger.info(f"Loading local model: {model_name}", module="ai")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto"
            )

            logger.info(f"Model {model_name} loaded successfully", module="ai")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}", module="ai")
            # Try fallback to a simpler model
            return self._load_fallback_model()

    def _load_fallback_model(self) -> bool:
        """Load a simple fallback model if the main model fails"""
        try:
            fallback_model = "microsoft/phi-2"  # Simple, reliable fallback
            logger.info(f"Loading fallback model: {fallback_model}", module="ai")

            self.tokenizer = AutoTokenizer.from_pretrained(fallback_model)
            self.model = AutoModelForCausalLM.from_pretrained(
                fallback_model,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto"
            )

            logger.info(f"Fallback model {fallback_model} loaded successfully", module="ai")
            return True
        except Exception as e:
            logger.error(f"Failed to load fallback model: {str(e)}", module="ai")
            return False

    @log_execution_time
    def generate_text(self, prompt: str, max_length: Optional[int] = None, temperature: Optional[float] = None) -> Optional[str]:
        """Generate text using OpenRouter (preferred) or local model"""
        try:
            # Try OpenRouter first if API key is available
            if self.ai_config.get('api_key'):
                logger.info("Attempting to use OpenRouter API", module="ai")
                openrouter_models = self.ai_config.get('openrouter_models', [])
                model = openrouter_models[0] if openrouter_models else None
                result = self.call_openrouter(prompt, model)
                if result:
                    logger.info("Text generated successfully via OpenRouter", module="ai", response_length=len(result))
                    return result
                else:
                    logger.warning("OpenRouter failed, falling back to local model", module="ai")

            # Fallback to local model
            if not self.model or not self.tokenizer:
                if not self.load_model():
                    logger.error("Failed to load any model", module="ai")
                    return None

            max_length = max_length or self.ai_config['max_tokens']
            temperature = temperature or self.ai_config['temperature']

            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                temperature=temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )

            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            logger.info("Text generated successfully via local model", module="ai", response_length=len(response))
            return response
        except Exception as e:
            logger.error(f"Text generation failed: {str(e)}", module="ai")
            return None

    @log_execution_time
    def analyze_image(self, image_path: str, task: str = "object_detection") -> Optional[Dict[str, Any]]:
        """Analyze image using vision models"""
        try:
            image_pipeline = pipeline(task, device=self.device)
            results = image_pipeline(str(image_path))
            logger.info(f"Image analysis completed: {task}", module="ai")
            return results
        except Exception as e:
            logger.error(f"Image analysis failed: {str(e)}", module="ai")
            return None

    def call_openrouter(self, prompt: str, model: Optional[str] = None) -> Optional[str]:
        """Call OpenRouter API for text generation with free Deepseek R1 model"""
        try:
            # Use the DeepSeek R1 model by default (best free model)
            if not model:
                free_models = self.ai_config.get('model_categories', {}).get('free_models', [])
                model = free_models[0] if free_models else "deepseek/deepseek-r1-0528:free"

            # Check if API key is available (optional for free models like DeepSeek R1)
            api_key = self.ai_config.get('api_key')
            
            # Some free models like DeepSeek R1 might work without API key
            headers = {
                "Content-Type": "application/json",
                "HTTP-Referer": "https://cert-me-boi.com",  # Add referer for better tracking
                "X-Title": "Cert Me Boi - Course Automation"  # Add title for better tracking
            }
            
            # Add authorization header if API key is available
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            else:
                logger.info(f"No API key provided, attempting to use free model: {model}", module="ai")

            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.ai_config.get('temperature', 0.7),
                "max_tokens": self.ai_config.get('max_tokens', 1000)  # Increased for R1 model
            }

            logger.info(f"Calling OpenRouter API with model: {model}", module="ai")
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60  # Increased timeout for R1 model (reasoning takes time)
            )

            if response.status_code == 200:
                result = response.json()
                text = result['choices'][0]['message']['content']
                usage = result.get('usage', {})
                logger.info("OpenRouter API call successful", module="ai",
                          model=model, tokens_used=usage.get('total_tokens', 0))
                
                # Log special success for DeepSeek R1
                if model == "deepseek/deepseek-r1-0528:free":
                    logger.info("🚀 DeepSeek R1 model used successfully - o1-level performance!", module="ai")
                
                return text
            elif response.status_code == 401:
                logger.error("OpenRouter API key invalid or expired", module="ai")
                if not api_key:
                    logger.info("Try getting a free API key from https://openrouter.ai for better access", module="ai")
                return None
            elif response.status_code == 429:
                logger.warning("OpenRouter API rate limit exceeded, falling back to local model", module="ai")
                return None
            else:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}", module="ai")
                return None
        except requests.exceptions.Timeout:
            logger.warning("OpenRouter API request timed out (R1 reasoning can take time), falling back to local model", module="ai")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API request failed: {str(e)}", module="ai")
            return None
        except Exception as e:
            logger.error(f"OpenRouter API call failed: {str(e)}", module="ai")
            return None

    def extract_text_from_image(self, image_path: str) -> Optional[str]:
        """Extract text from image using OCR"""
        try:
            ocr = pipeline("image-to-text", device=self.device)
            result = ocr(str(image_path))
            text = " ".join([item['generated_text'] for item in result])
            logger.info("Text extracted from image", module="ai", length=len(text))
            return text
        except Exception as e:
            logger.error(f"OCR failed: {str(e)}", module="ai")
            return None

    def answer_question(self, question: str, context: str) -> Optional[str]:
        """Answer a question based on context"""
        try:
            qa_pipeline = pipeline("question-answering", device=self.device)
            result = qa_pipeline(question=question, context=context)
            logger.info("Question answered", module="ai", confidence=result['score'])
            return result['answer']
        except Exception as e:
            logger.error(f"Question answering failed: {str(e)}", module="ai")
            return None

    def classify_text(self, text: str, labels: List[str]) -> Optional[Dict[str, float]]:
        """Classify text into predefined labels"""
        try:
            classifier = pipeline("zero-shot-classification", device=self.device)
            result = classifier(text, labels)
            logger.info("Text classification completed", module="ai")
            return dict(zip(result['labels'], result['scores']))
        except Exception as e:
            logger.error(f"Text classification failed: {str(e)}", module="ai")
            return None

    def summarize_text(self, text: str, max_length: Optional[int] = None) -> Optional[str]:
        """Generate a summary of the input text"""
        try:
            summarizer = pipeline("summarization", device=self.device)
            max_length = max_length or min(len(text.split()) // 2, 150)
            result = summarizer(text, max_length=max_length, min_length=30)
            logger.info("Text summarization completed", module="ai", length=len(result[0]['summary_text']))
            return result[0]['summary_text']
        except Exception as e:
            logger.error(f"Text summarization failed: {str(e)}", module="ai")
            return None

    def cleanup(self) -> None:
        """Clean up model resources"""
        try:
            if self.model:
                del self.model
            if self.tokenizer:
                del self.tokenizer
            torch.cuda.empty_cache()
            logger.info("Model resources cleaned up", module="ai")
        except Exception as e:
            logger.error(f"Model cleanup failed: {str(e)}", module="ai")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
        if exc_type:
            logger.error(f"Error in context: {str(exc_val)}", module="ai")

    def get_available_models(self) -> Dict[str, List[str]]:
        """Get list of available models categorized by type"""
        return {
            'free_models': self.ai_config.get('model_categories', {}).get('free_models', []),
            'premium_models': self.ai_config.get('model_categories', {}).get('premium_models', []),
            'openrouter_models': self.ai_config.get('openrouter_models', [])
        }

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a specific model using exact dictionary matching"""
        # Default model info structure
        model_info = {
            'name': model_name,
            'provider': 'unknown',
            'is_free': False,
            'description': '',
            'recommended_for': []
        }

        # Check if model exists in our metadata dictionary
        if model_name in self.MODEL_METADATA:
            metadata = self.MODEL_METADATA[model_name]
            model_info.update(metadata)
            logger.info(f"Model info retrieved from metadata dictionary", module="ai", model=model_name)
        else:
            # Fallback to config-based categorization for unknown models
            free_models = self.ai_config.get('model_categories', {}).get('free_models', [])
            premium_models = self.ai_config.get('model_categories', {}).get('premium_models', [])

            if model_name in free_models:
                model_info['provider'] = 'openrouter'
                model_info['is_free'] = True
                model_info['description'] = 'Free model (not in metadata dictionary)'
                model_info['recommended_for'] = ['general tasks']
            elif model_name in premium_models:
                model_info['provider'] = 'openrouter'
                model_info['is_free'] = False
                model_info['description'] = 'Premium model (not in metadata dictionary)'
                model_info['recommended_for'] = ['complex tasks']
            else:
                logger.warning(f"Model {model_name} not found in metadata or config", module="ai")

        return model_info

    def set_model(self, model_name: str) -> bool:
        """Set the default model for text generation"""
        try:
            available_models = self.get_available_models()
            all_models = available_models['free_models'] + available_models['premium_models']

            if model_name in all_models:
                self.ai_config['default_model'] = model_name
                logger.info(f"Default model set to: {model_name}", module="ai")
                return True
            else:
                logger.error(f"Model {model_name} not found in available models", module="ai")
                return False
        except Exception as e:
            logger.error(f"Failed to set model: {str(e)}", module="ai")
            return False

    def test_model_connection(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Test connection to a specific model"""
        try:
            model_name = model_name or self.ai_config['default_model']
            test_prompt = "Hello, this is a test message. Please respond with 'Connection successful' if you can see this."

            result = {
                'model': model_name,
                'status': 'unknown',
                'response': None,
                'error': None,
                'provider': 'unknown'
            }

            # Try OpenRouter first
            if self.ai_config.get('api_key'):
                response = self.call_openrouter(test_prompt, model_name)
                if response:
                    result['status'] = 'success'
                    result['response'] = response
                    result['provider'] = 'openrouter'
                    return result

            # Try local model
            if self.model and self.tokenizer:
                response = self.generate_text(test_prompt)
                if response:
                    result['status'] = 'success'
                    result['response'] = response
                    result['provider'] = 'local'
                    return result

            result['status'] = 'failed'
            result['error'] = 'No working model found'
            return result

        except Exception as e:
            return {
                'model': model_name,
                'status': 'error',
                'response': None,
                'error': str(e),
                'provider': 'unknown'
            }

if __name__ == "__main__":
    # Test the model handler
    with ModelHandler() as handler:
        # Test text generation
        text = handler.generate_text("What is machine learning?")
        print(f"Generated text: {text}")

        # Test image analysis
        image_path = "data/screenshots/test.png"
        if Path(image_path).exists():
            results = handler.analyze_image(image_path)
            print(f"Image analysis results: {results}") 