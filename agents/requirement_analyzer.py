#!/usr/bin/env python
import json
import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RequirementAnalyzer:
    def __init__(self, model_manager, rag_system):
        self.model_manager = model_manager
        self.rag_system = rag_system
        self.model = "deepseek-coder-v2:16b"  # Using deepseek-coder-v2:16b model for requirement analysis

    def analyze(self, user_prompt: str) -> Dict[str, Any]:
        """
        Analyze the user's requirements and extract structured information.
        
        Args:
            user_prompt: The user's description of the project
            
        Returns:
            A dictionary containing the analyzed requirements
        """
        logger.info(f"Analyzing requirements from prompt: {user_prompt[:100]}...")
        
        # Get relevant context from RAG system
        context = self.rag_system.query(
            f"project requirements for {user_prompt}",
            "project_requirements"
        )
        
        # Prepare the prompt for the LLM
        prompt = f"""
        Task: Analyze the following project requirements and extract structured information.
        
        User's Project Description:
        {user_prompt}
        
        Additional Context:
        {context}
        
        Instructions:
        1. Analyze the user's requirements carefully
        2. Extract key information about the project
        3. Identify the project type, features, and technical requirements
        4. Suggest appropriate packages and frameworks
        5. Return a JSON object with the following structure:
        
        {{
            "project_type": "Brief description of the project type (e.g., web app, CLI tool, data analysis)",
            "description": "A detailed description of the project",
            "features": [
                {{"name": "Feature name", "description": "Feature description", "priority": "high|medium|low"}}
            ],
            "database_required": true|false,
            "database_type": "sql|nosql|none",
            "has_frontend": true|false,
            "suggested_frameworks": ["framework1", "framework2"],
            "suggested_packages": ["package1", "package2"],
            "file_structure": [
                {{"path": "file_or_directory_path", "type": "file|directory", "description": "brief_description"}}
            ]
        }}
        
        Return only valid JSON, no other text.
        """
        
        # Generate requirements using the model
        try:
            response = self.model_manager.generate(prompt=prompt, model=self.model)
            if isinstance(response, str):
                # Try to parse string response
                try:
                    # Extract JSON from code block if present
                    json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
                    if json_match:
                        response = json_match.group(1)
                    requirements = json.loads(response)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing failed: {e}\nRaw response: {response}")
                    requirements = {
                        'components': ['Task Manager Interface', 'Database Integration'],
                        'structure': ['Basic CRUD Operations', 'Task Filtering']
                    }
            elif isinstance(response, dict):
                # Use response directly
                requirements = response
            else:
                raise ValueError(f"Unexpected response type: {type(response)}")
            
            # Validate and ensure required fields
            requirements = self._validate_requirements(requirements)
            logger.info("Successfully analyzed requirements")
            logger.debug(f"Final requirements: {requirements}")
            return requirements
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse model response as JSON: {e}\nRaw response: {response}")
            logger.error('Invalid JSON format in analysis response')
            return self._get_default_requirements()
        except Exception as e:
            logger.error(f"Error analyzing requirements: {e}")
            return self._get_default_requirements()

    def _validate_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and ensure the requirements dictionary has all required fields."""
        # Ensure required fields exist
        required_fields = [
            "project_type", "description", "features", 
            "database_required", "has_frontend", 
            "suggested_frameworks", "suggested_packages"
        ]
        
        for field in required_fields:
            if field not in requirements:
                if field in ["features", "suggested_frameworks", "suggested_packages"]:
                    requirements[field] = []
                elif field in ["database_required", "has_frontend"]:
                    requirements[field] = False
                else:
                    requirements[field] = "Not specified"
        
        # Ensure database_type exists if database_required is True
        if requirements.get("database_required", False) and "database_type" not in requirements:
            requirements["database_type"] = "sql"  # Default to SQL
        
        # Ensure features have all required fields
        for feature in requirements.get("features", []):
            if "name" not in feature:
                feature["name"] = "Unnamed Feature"
            if "description" not in feature:
                feature["description"] = "No description provided"
            if "priority" not in feature:
                feature["priority"] = "medium"
                
        return requirements

    def _get_default_requirements(self) -> Dict[str, Any]:
        """Return default requirements for a calculator project."""
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
