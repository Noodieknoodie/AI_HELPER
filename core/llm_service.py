# core/llm_service.py
import os
import json
import requests
from typing import Dict, Any, Optional, Callable

class LLMService:
    """Service for interacting with LLM APIs."""
    
    def __init__(self, config: Dict, api_key: Optional[str] = None):
        """Initialize the LLM service.
        
        Args:
            config: Configuration dictionary.
            api_key: API key for the service.
        """
        self.config = config
        self.api_key = api_key
        self.api_provider = config.get("default_api", "anthropic")
        self.api_config = config["api"].get(self.api_provider, {})
        
        # Set default model
        self.model_id = self.api_config.get("default_model")
        
        # Default parameters
        self.parameters = {
            "temperature": 0.7,
            "max_tokens": 4000
        }
        
        # Extended thinking settings
        self.use_extended_thinking = False
        self.extended_thinking_budget = 16000
    
    def set_api_key(self, api_key: str):
        """Set the API key.
        
        Args:
            api_key: API key for the service.
        """
        self.api_key = api_key
    
    def set_provider(self, provider: str):
        """Set the LLM provider.
        
        Args:
            provider: Provider name ("anthropic" or "openai").
            
        Returns:
            Boolean indicating success.
        """
        if provider in self.config["api"]:
            self.api_provider = provider
            self.api_config = self.config["api"][provider]
            self.model_id = self.api_config.get("default_model")
            return True
        return False
    
    def set_model(self, model_id: str):
        """Set the model to use.
        
        Args:
            model_id: ID of the model to use.
        """
        self.model_id = model_id
        
        # Adjust default max_tokens based on model capabilities
        model_caps = self._get_model_capabilities()
        if model_caps:
            self.parameters["max_tokens"] = model_caps.get("max_tokens_default", 4000)
    
    def set_parameter(self, param_name: str, value: Any):
        """Set a parameter value.
        
        Args:
            param_name: Name of the parameter.
            value: Value to set.
        """
        self.parameters[param_name] = value
    
    def set_extended_thinking(self, enabled: bool, budget: Optional[int] = None):
        """Enable or disable extended thinking mode.
        
        Args:
            enabled: Whether to enable extended thinking.
            budget: Token budget for extended thinking (optional).
            
        Returns:
            Boolean indicating success.
        """
        model_caps = self._get_model_capabilities()
        if not model_caps.get("supports_extended_thinking", False) and enabled:
            return False
        
        self.use_extended_thinking = enabled
        if budget is not None:
            max_budget = model_caps.get("max_tokens_extended", 16000)
            self.extended_thinking_budget = min(budget, max_budget)
        return True
    
    def _get_model_capabilities(self):
        """Get capabilities for the current model.
        
        Returns:
            Dictionary of model capabilities or empty dict if not found.
        """
        for model in self.api_config.get("models", []):
            if model.get("id") == self.model_id:
                return model.get("capabilities", {})
        return {}
    
    def get_available_providers(self):
        """Get available LLM providers.
        
        Returns:
            List of provider names.
        """
        return list(self.config["api"].keys())
    
    def get_available_models(self, provider: Optional[str] = None):
        """Get available models for a provider.
        
        Args:
            provider: Provider name. If None, uses the current provider.
            
        Returns:
            List of model information dictionaries.
        """
        provider = provider or self.api_provider
        return self.config["api"].get(provider, {}).get("models", [])
    
    def send_request(self, prompt: str, on_progress: Optional[Callable[[int], None]] = None) -> str:
        """Send a request to the LLM API.
        
        Args:
            prompt: The prompt text to send.
            on_progress: Callback function for progress updates.
            
        Returns:
            Response text or error message.
        """
        if not self.api_key:
            return "Error: API key not provided"
        
        if not self.model_id:
            return "Error: No model selected"
        
        # Report initial progress
        if on_progress:
            on_progress(10)
        
        try:
            if self.api_provider == "anthropic":
                return self._anthropic_request(prompt, on_progress)
            elif self.api_provider == "openai":
                return self._openai_request(prompt, on_progress)
            else:
                return f"Error: Unsupported provider {self.api_provider}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _anthropic_request(self, prompt: str, on_progress: Optional[Callable[[int], None]] = None) -> str:
        """Send a request to the Anthropic API.
        
        Args:
            prompt: The prompt text to send.
            on_progress: Callback function for progress updates.
            
        Returns:
            Response text or error message.
        """
        api_url = self.api_config.get("url", "https://api.anthropic.com/v1/messages")
        api_version = self.api_config.get("version", "2023-06-01")
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": api_version,
            "content-type": "application/json"
        }
        
        # Add long output header for Claude 3.7 Sonnet if supported
        model_caps = self._get_model_capabilities()
        if model_caps.get("supports_long_output", False):
            headers["anthropic-beta"] = "output-128k-2025-02-19"
        
        data = {
            "model": self.model_id,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        # Add extended thinking if enabled and supported
        if self.use_extended_thinking and model_caps.get("supports_extended_thinking", False):
            data["thinking"] = {
                "type": "enabled",
                "budget_tokens": self.extended_thinking_budget
            }
        
        # Add parameters
        for param, value in self.parameters.items():
            data[param] = value
        
        # Update progress
        if on_progress:
            on_progress(30)
        
        # Send request
        response = requests.post(api_url, headers=headers, json=data)
        
        # Update progress
        if on_progress:
            on_progress(90)
        
        if response.status_code == 200:
            result = response.json()
            # Extract text from response
            if "content" in result and len(result["content"]) > 0:
                response_text = ""
                # Process all content blocks
                for content_block in result["content"]:
                    if content_block.get("type") == "text":
                        response_text += content_block.get("text", "")
                
                # Final progress
                if on_progress:
                    on_progress(100)
                    
                return response_text
            else:
                return "Error: Empty response from API"
        else:
            return f"Error: API returned status code {response.status_code}\n{response.text}"
    
    def _openai_request(self, prompt: str, on_progress: Optional[Callable[[int], None]] = None) -> str:
        """Send a request to the OpenAI API.
        
        Args:
            prompt: The prompt text to send.
            on_progress: Callback function for progress updates.
            
        Returns:
            Response text or error message.
        """
        api_url = self.api_config.get("url", "https://api.openai.com/v1/chat/completions")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_id,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        # Add parameters
        for param, value in self.parameters.items():
            data[param] = value
        
        # Update progress
        if on_progress:
            on_progress(30)
        
        # Send request
        response = requests.post(api_url, headers=headers, json=data)
        
        # Update progress
        if on_progress:
            on_progress(90)
        
        if response.status_code == 200:
            result = response.json()
            # Extract text from response
            if "choices" in result and len(result["choices"]) > 0:
                response_text = result["choices"][0]["message"]["content"]
                
                # Final progress
                if on_progress:
                    on_progress(100)
                    
                return response_text
            else:
                return "Error: Empty response from API"
        else:
            return f"Error: API returned status code {response.status_code}\n{response.text}"