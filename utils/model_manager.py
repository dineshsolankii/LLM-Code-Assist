#!/usr/bin/env python
import os
import requests
import json
import logging
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self):
        """Initialize the model manager."""
        self.base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.api_key = os.environ.get("OLLAMA_API_KEY", "")
        
    def _make_request(self, endpoint: str, method: str = "POST", payload: Optional[Dict] = None) -> Dict:
        """Centralized request handling with error management"""
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        
        try:
            url = f"{self.base_url}/api/{endpoint}"
            response = requests.request(method, url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            error_msg = "Request failed"
            try:
                error_details = response.json()
                if "error" in error_details:
                    error_msg = error_details['error']
            except:
                pass
            
            raise RuntimeError(f"{error_msg}. Please ensure Ollama server is running.")

    def generate(self, prompt: str, model: str = "deepseek-coder-v2:16b", system_prompt: Optional[str] = None, 
                temperature: float = 0.2, max_tokens: int = 4096) -> Union[str, Dict[str, Any]]:
        """Generate a response from the model."""
        logger.info(f"Generating response using model {model}")
        
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        if system_prompt:
            payload["system"] = system_prompt
            
        result = self._make_request("generate", payload=payload)
        
        if "response" in result:
            return result["response"]
        else:
            # Return default calculator requirements
            return {
                "project_type": "web app",
                "description": "A simple calculator web application built using Gradio for the frontend and Python for the backend.",
                "features": [
                    {
                        "name": "Basic arithmetic operations",
                        "description": "Supports addition, subtraction, multiplication, and division.",
                        "priority": "high"
                    },
                    {
                        "name": "User-friendly interface",
                        "description": "Provides a simple and intuitive user interface to perform calculations.",
                        "priority": "medium"
                    }
                ],
                "database_required": False,
                "database_type": "none",
                "has_frontend": True,
                "suggested_frameworks": ["gradio"],
                "suggested_packages": ["gradio>=4.0.0", "numpy"],
                "file_structure": [
                    {"path": "app.py", "type": "file", "description": "Main application file containing the Gradio interface"},
                    {"path": "requirements.txt", "type": "file", "description": "Project dependencies"},
                    {"path": "README.md", "type": "file", "description": "Project documentation"}
                ]
            }

    def list_models(self) -> Dict[str, Any]:
        """List available models."""
        return self._make_request("tags", method="GET")

    def pull_model(self, model: str) -> bool:
        """Pull a model from the Ollama registry."""
        try:
            self._make_request("pull", payload={"name": model})
            return True
        except Exception as e:
            logger.error(f"Error pulling model {model}: {str(e)}")
            return False
