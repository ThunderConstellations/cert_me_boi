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
        """Load the specified model or default model"""
        try:
            model_name = model_name or self.ai_config['default_model']
            logger.info(f"Loading model: {model_name}", module="ai")

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
            return False

    @log_execution_time
    def generate_text(self, prompt: str, max_length: Optional[int] = None, temperature: Optional[float] = None) -> Optional[str]:
        """Generate text using the loaded model"""
        try:
            if not self.model or not self.tokenizer:
                if not self.load_model():
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
            logger.info("Text generated successfully", module="ai", length=len(response))
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
        """Call OpenRouter API for text generation"""
        if not self.ai_config.get('api_key'):
            logger.warning("OpenRouter API key not configured", module="ai")
            return None

        try:
            model = model or self.ai_config['openrouter_models'][0]
            headers = {
                "Authorization": f"Bearer {self.ai_config['api_key']}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.ai_config['temperature']
            }

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result['choices'][0]['message']['content']
                logger.info("OpenRouter API call successful", module="ai", model=model)
                return text
            else:
                logger.error(f"OpenRouter API error: {response.status_code}", module="ai")
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