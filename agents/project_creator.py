#!/usr/bin/env python
import os
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ProjectCreator:
    def __init__(self, model_manager, rag_system, file_manager):
        self.model_manager = model_manager
        self.rag_system = rag_system
        self.file_manager = file_manager
        self.model = "deepseek-coder-v2:16b"

    def create_project(self, requirements: Dict[str, Any], framework: str, project_name: str) -> str:
        """Create the project structure based on requirements and framework."""
        try:
            logger.info(f"Creating project structure for {project_name} using {framework}")
            
            # Validate inputs
            if not project_name or not isinstance(project_name, str):
                raise ValueError(f"Invalid project name: {project_name}")
                
            if not framework or not isinstance(framework, str):
                raise ValueError(f"Invalid framework: {framework}")
                
            if not requirements or not isinstance(requirements, dict):
                raise ValueError(f"Invalid requirements: {requirements}")
            
            # If requirements doesn't have file_structure, generate it
            if "file_structure" not in requirements or not requirements["file_structure"]:
                logger.info(f"Generating file structure for {project_name}")
                requirements["file_structure"] = self._generate_file_structure(requirements, framework)
            
            # Ensure file_structure is a list
            if not isinstance(requirements["file_structure"], list):
                logger.warning(f"file_structure is not a list, converting: {requirements['file_structure']}")
                requirements["file_structure"] = []
            
            # Create the file structure
            logger.info(f"Creating file structure with {len(requirements['file_structure'])} items")
            self.file_manager.create_project_structure(project_name, requirements["file_structure"])
            
            # Create requirements.txt
            logger.info(f"Creating requirements.txt for {project_name}")
            self._create_requirements_file(project_name, requirements, framework)
            
            # Create README.md
            logger.info(f"Creating README.md for {project_name}")
            self._create_readme_file(project_name, requirements, framework)
            
            project_path = self.file_manager.get_project_path(project_name)
            logger.info(f"Project {project_name} created successfully at {project_path}")
            return project_path
            
        except Exception as e:
            logger.error(f"Error creating project {project_name}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def _generate_file_structure(self, requirements: Dict[str, Any], framework: str) -> List[Dict[str, str]]:
        """Generate the file structure based on requirements and framework."""
        # Get relevant context from RAG system
        context = self.rag_system.query(
            f"project structure for {framework} {requirements['project_type']}",
            "project_structure"
        )
        
        # Prepare the prompt for the LLM
        prompt = f"""
        Generate a comprehensive file structure for a {framework} project with the following requirements:
        
        Project Type: {requirements['project_type']}
        Features: {json.dumps(requirements['features'])}
        Database Required: {requirements['database_required']}
        Has Frontend: {requirements['has_frontend']}
        
        Additional Context: {context}
        
        Return a JSON array with the following structure:
        [
            {{
                "path": "file_or_directory_path",
                "type": "file|directory",
                "description": "brief_description"
            }}
        ]
        
        Include all necessary files and directories for a {framework} project.
        Ensure the structure is comprehensive and includes:
        1. All necessary configuration files
        2. Source code files for the main functionality
        3. Template/view files if frontend is required
        4. Database models if database is required
        5. Test files for unit/integration testing
        6. Documentation files
        
        Return only valid JSON, no other text.
        """
        
        # Get response from the model
        response = self.model_manager.generate(self.model, prompt)
        
        try:
            # Clean response and parse JSON
            response_text = response.strip()
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Parse the JSON
            file_structure = json.loads(response_text)
            
            # Ensure all entries have the required fields
            for item in file_structure:
                if "path" not in item or "type" not in item:
                    raise KeyError(f"Missing required field in file structure item: {item}")
                
                # Add description if missing
                if "description" not in item:
                    item["description"] = f"{item['type'].capitalize()} for the project"
            
            return file_structure
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing file structure: {e}")
            return self._get_default_file_structure(framework)

    def _get_default_file_structure(self, framework: str) -> List[Dict[str, str]]:
        """Get default file structure for a framework."""
        if framework == "python":
            return [
                {"path": "main.py", "type": "file", "description": "Main entry point"},
                {"path": "requirements.txt", "type": "file", "description": "Project dependencies"},
                {"path": "README.md", "type": "file", "description": "Project documentation"},
                {"path": "src", "type": "directory", "description": "Source code directory"},
                {"path": "src/__init__.py", "type": "file", "description": "Makes src a Python package"},
                {"path": "tests", "type": "directory", "description": "Test files directory"},
                {"path": "tests/__init__.py", "type": "file", "description": "Makes tests a Python package"}
            ]
        elif framework == "gradio":
            return [
                {"path": "app.py", "type": "file", "description": "Main Gradio application"},
                {"path": "requirements.txt", "type": "file", "description": "Project dependencies"},
                {"path": "README.md", "type": "file", "description": "Project documentation"},
                {"path": "src", "type": "directory", "description": "Source code directory"},
                {"path": "src/__init__.py", "type": "file", "description": "Makes src a Python package"},
                {"path": "src/model.py", "type": "file", "description": "Model implementation"},
                {"path": "src/utils.py", "type": "file", "description": "Utility functions"},
                {"path": "tests", "type": "directory", "description": "Test files directory"},
                {"path": "tests/__init__.py", "type": "file", "description": "Makes tests a Python package"}
            ]
        else:
            return [
                {"path": "main.py", "type": "file", "description": "Main entry point"},
                {"path": "requirements.txt", "type": "file", "description": "Project dependencies"},
                {"path": "README.md", "type": "file", "description": "Project documentation"}
            ]

    def _create_requirements_file(self, project_name: str, requirements: Dict[str, Any], framework: str) -> None:
        """Create requirements.txt file."""
        deps = ["pytest"]  # Basic testing dependency
        
        if framework == "gradio":
            deps.extend(["gradio>=4.0.0", "numpy", "pillow"])
        
        # Add any additional dependencies from requirements
        if "suggested_packages" in requirements and isinstance(requirements["suggested_packages"], list):
            deps.extend(requirements["suggested_packages"])
        
        # Write requirements file
        content = "\n".join(sorted(set(deps)))
        self.file_manager.write_file(project_name, "requirements.txt", content)

    def _create_readme_file(self, project_name: str, requirements: Dict[str, Any], framework: str) -> None:
        """Create README.md file."""
        project_type = requirements.get("project_type", "Python Project")
        description = requirements.get("description", "")
        
        # Handle features properly based on their type
        features = requirements.get("features", [])
        features_str = ""
        
        for feature in features:
            if isinstance(feature, str):
                features_str += f"- {feature}\n"
            elif isinstance(feature, dict) and "name" in feature:
                feature_desc = feature.get("description", "")
                if feature_desc:
                    features_str += f"- **{feature['name']}**: {feature_desc}\n"
                else:
                    features_str += f"- {feature['name']}\n"
        
        if not features_str:
            features_str = "- No specific features listed"
        
        content = f"""# {project_name}

{project_type}

## Description
{description}

## Features
{features_str}

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the project:
   ```bash
   python {"app.py" if framework == "gradio" else "main.py"}
   ```

## Usage
{self._get_usage_instructions(framework)}
"""
        self.file_manager.write_file(project_name, "README.md", content)

    def _get_usage_instructions(self, framework: str) -> str:
        """Get framework-specific usage instructions."""
        if framework == "django":
            return """1. Apply migrations: `python manage.py migrate`
2. Create superuser: `python manage.py createsuperuser`
3. Run development server: `python manage.py runserver`"""
        elif framework == "flask":
            return """1. Set environment variables:
   - `export FLASK_APP=app.py` (Unix/MacOS)
   - `set FLASK_APP=app.py` (Windows)
2. Run development server: `flask run`"""
        elif framework == "streamlit":
            return "Run the app: `streamlit run app.py`"
        else:
            return "Run the script: `python main.py`"
