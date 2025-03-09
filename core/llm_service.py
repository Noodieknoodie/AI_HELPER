# core/llm_service.py
import os
import json
import requests
import anthropic
import openai
import google.generativeai as genai
from typing import Dict, Any, Optional, Callable
import importlib.util

class LLMService:
    def __init__(self, config: Dict, api_key: Optional[str] = None):
        self.config = config
        self.api_key = api_key
        self.api_provider = config.get("default_api", "anthropic")
        self.api_config = config["api"].get(self.api_provider, {})

        # Set default model ID but don't configure parameters yet
        self.model_id = self.api_config.get("default_model")

        # Only initialize universal parameters
        self.parameters = {
            "temperature": 0.7
        }

        # Track usage
        self.last_usage = {}
        
        # Initialize provider-specific clients as needed
        self.gemini_client = None

        # Configure parameters once we know which model we're using
        if self.model_id:
            self.configure_for_model()

        # Initialize reasoning settings
        self.reasoning_effort = "medium"

    
    def configure_for_model(self):
        """Configure optimal parameters based on selected model capabilities."""
        if not self.model_id:
            return
            
        model_caps = self._get_model_capabilities()
        if not model_caps:
            return
        
        # Set appropriate max_tokens based on model capabilities
        if self.api_provider == "anthropic":
            self.parameters["max_tokens"] = model_caps.get("max_tokens_default", 8192)
            
            # Only initialize extended thinking if supported
            if model_caps.get("supports_extended_thinking", False):
                self.use_extended_thinking = False
                self.extended_thinking_budget = model_caps.get("max_tokens_extended", 64000)
                
        elif self.api_provider == "openai":
            # For OpenAI reasoning models, handle differently
            if model_caps.get("supports_reasoning", False):
                self.parameters["max_tokens"] = model_caps.get("max_tokens_default", 16000)
                self.reasoning_effort = "medium"
            else:
                # For regular GPT models
                self.parameters["max_tokens"] = model_caps.get("max_tokens_default", 16384)
        
        elif self.api_provider == "gemini":
            self.parameters["max_output_tokens"] = model_caps.get("output_token_limit", 8192)
            
            # Initialize thinking for thinking models
            if model_caps.get("supports_thinking", False):
                self.use_thinking = False
    
    def _initialize_gemini_client(self):
        """Initialize the Google Gemini client if needed."""
        if self.gemini_client is None and self.api_key:
            try:
                # Check if google.genai is installed
                if importlib.util.find_spec("google.genai") is None:
                    return "Error: google-genai package is not installed. Please install it with 'pip install google-genai'"
                
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.gemini_client = genai
                return None
            except ImportError:
                return "Error: Could not import google-genai. Please install it with 'pip install google-genai'"
            except Exception as e:
                return f"Error initializing Gemini client: {str(e)}"
        return None
    
    def set_api_key(self, api_key: str):
        self.api_key = api_key
        
        # Reset client if provider is Gemini
        if self.api_provider == "gemini":
            self.gemini_client = None
    
    def set_provider(self, provider: str):
        if provider in self.config["api"]:
            previous_provider = self.api_provider
            self.api_provider = provider
            self.api_config = self.config["api"][provider]
            self.model_id = self.api_config.get("default_model")
            
            # Clear any model-specific attributes
            for attr in ['use_extended_thinking', 'extended_thinking_budget', 
                         'reasoning_effort', 'use_thinking']:
                if hasattr(self, attr):
                    delattr(self, attr)
            
            # Clear provider-specific clients if changing providers
            if previous_provider != provider and provider == "gemini":
                self.gemini_client = None
            
            # Configure for new provider/model
            self.configure_for_model()
            return True
        return False
    
    def set_model(self, model_id: str):
        self.model_id = model_id
        
        # Clear any model-specific attributes
        for attr in ['use_extended_thinking', 'extended_thinking_budget', 'reasoning_effort']:
            if hasattr(self, attr):
                delattr(self, attr)
        
        # Configure for new model
        self.configure_for_model()
    
    def set_parameter(self, param_name: str, value: Any):
        self.parameters[param_name] = value
    
    def set_extended_thinking(self, enabled: bool, budget: Optional[int] = None):
        model_caps = self._get_model_capabilities()
        if not model_caps.get("supports_extended_thinking", False):
            return False
        
        self.use_extended_thinking = enabled
        if budget is not None:
            max_budget = model_caps.get("max_tokens_extended", 64000)
            self.extended_thinking_budget = min(budget, max_budget)
        return True
    
    def set_thinking(self, enabled: bool):
        """Enable or disable thinking for Gemini models that support it."""
        model_caps = self._get_model_capabilities()
        if not model_caps.get("supports_thinking", False):
            return False
        
        self.use_thinking = enabled
        return True
    
    def set_reasoning_effort(self, effort: str):
        model_caps = self._get_model_capabilities()
        if not model_caps.get("supports_reasoning", False):
            return False
        
        if effort not in ['low', 'medium', 'high']:
            return False
        
        self.reasoning_effort = effort
        return True
    
    def _get_model_capabilities(self):
        for model in self.api_config.get("models", []):
            if model.get("id") == self.model_id:
                return model.get("capabilities", {})
        return {}
    
    def get_available_providers(self):
        return list(self.config["api"].keys())
    
    def get_available_models(self, provider: Optional[str] = None):
        provider = provider or self.api_provider
        return self.config["api"].get(provider, {}).get("models", [])
    
    def send_request(self, prompt: str, on_progress: Optional[Callable[[int], None]] = None) -> str:
        if not self.api_key:
            return "Error: API key not provided"
        
        if not self.model_id:
            return "Error: No model selected"
        
        if on_progress:
            on_progress(10)
        
        try:
            if self.api_provider == "anthropic":
                return self._anthropic_request(prompt, on_progress)
            elif self.api_provider == "openai":
                return self._openai_request(prompt, on_progress)
            elif self.api_provider == "gemini":
                return self._gemini_request(prompt, on_progress)
            else:
                return f"Error: Unsupported provider {self.api_provider}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _anthropic_request(self, prompt: str, on_progress: Optional[Callable[[int], None]] = None) -> str:
        api_url = self.api_config.get("url", "https://api.anthropic.com/v1/messages")
        api_version = self.api_config.get("version", "2023-06-01")
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": api_version,
            "content-type": "application/json"
        }
        
        model_caps = self._get_model_capabilities()
        if model_caps.get("supports_long_output", False):
            headers["anthropic-beta"] = "output-128k-2025-02-19"
        
        data = {
            "model": self.model_id,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        # Add extended thinking if supported and enabled
        if hasattr(self, 'use_extended_thinking') and self.use_extended_thinking and model_caps.get("supports_extended_thinking", False):
            data["thinking"] = {
                "type": "enabled",
                "budget_tokens": self.extended_thinking_budget
            }
        
        # Add other parameters
        for param, value in self.parameters.items():
            data[param] = value
        
        if on_progress:
            on_progress(30)
        
        response = requests.post(api_url, headers=headers, json=data)
        
        if on_progress:
            on_progress(90)
        
        if response.status_code == 200:
            result = response.json()
            if "content" in result and len(result["content"]) > 0:
                response_text = ""
                for content_block in result["content"]:
                    if content_block.get("type") == "text":
                        response_text += content_block.get("text", "")
                
                if "usage" in result:
                    self.last_usage = result["usage"]
                
                if on_progress:
                    on_progress(100)
                    
                return response_text
            else:
                return "Error: Empty response from API"
        else:
            return f"Error: API returned status code {response.status_code}\n{response.text}"
    
    def _openai_request(self, prompt: str, on_progress: Optional[Callable[[int], None]] = None) -> str:
        api_url = self.api_config.get("url", "https://api.openai.com/v1/chat/completions")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        model_caps = self._get_model_capabilities()
        
        data = {
            "model": self.model_id,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        # Configure request based on model type
        if model_caps.get("supports_reasoning", False):
            # For reasoning models, use max_completion_tokens
            if "max_tokens" in self.parameters:
                data["max_completion_tokens"] = self.parameters["max_tokens"]
            
            # Add reasoning_effort if available
            if hasattr(self, 'reasoning_effort'):
                data["reasoning_effort"] = self.reasoning_effort
        else:
            # For standard models, use max_tokens
            if "max_tokens" in self.parameters:
                data["max_tokens"] = self.parameters["max_tokens"]
        
        # Add remaining parameters
        for param, value in self.parameters.items():
            if param != "max_tokens" or not model_caps.get("supports_reasoning", False):
                data[param] = value
        
        if on_progress:
            on_progress(30)
        
        response = requests.post(api_url, headers=headers, json=data)
        
        if on_progress:
            on_progress(90)
        
        if response.status_code == 200:
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                response_text = result["choices"][0]["message"]["content"]
                
                if "usage" in result:
                    self.last_usage = result["usage"]
                
                if on_progress:
                    on_progress(100)
                    
                return response_text
            else:
                return "Error: Empty response from API"
        else:
            return f"Error: API returned status code {response.status_code}\n{response.text}"
    
    def _gemini_request(self, prompt: str, on_progress: Optional[Callable[[int], None]] = None) -> str:
        """Send a request to the Google Gemini API.
        
        Args:
            prompt: The prompt text to send.
            on_progress: Callback function for progress updates.
            
        Returns:
            Response text or error message.
        """
        # Initialize Gemini client if needed
        error = self._initialize_gemini_client()
        if error:
            return error
            
        if on_progress:
            on_progress(20)
            
        try:
            # Get model capabilities
            model_caps = self._get_model_capabilities()
            
            # Configure generation parameters
            generation_config = {
                "temperature": self.parameters.get("temperature", 0.7),
                "max_output_tokens": self.parameters.get("max_output_tokens", 8192),
                "top_p": self.parameters.get("top_p", 1.0),
                "top_k": self.parameters.get("top_k", 32)
            }
            
            # Create model
            model = self.gemini_client.GenerativeModel(
                model_name=self.model_id,
                generation_config=generation_config
            )
            
            if on_progress:
                on_progress(40)
                
            # Apply thinking if supported and enabled
            generation_options = {}
            if model_caps.get("supports_thinking", False) and getattr(self, 'use_thinking', False):
                generation_options["thinking"] = True
                
            # Send request with any options
            if generation_options:
                response = model.generate_content(prompt, generation_options=generation_options)
            else:
                response = model.generate_content(prompt)
            
            if on_progress:
                on_progress(90)
                
            # Store usage information
            if hasattr(response, "usage_metadata"):
                self.last_usage = {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count
                }
            
            if on_progress:
                on_progress(100)
                
            # Return the text response
            return response.text
        except Exception as e:
            return f"Error from Gemini API: {str(e)}"