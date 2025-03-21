#!/usr/bin/env python
import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CodeGenerator:
    def __init__(self, model_manager, rag_system, file_manager):
        self.model_manager = model_manager
        self.rag_system = rag_system
        self.file_manager = file_manager
        self.model = "deepseek-coder-v2:16b"  # Using the 16B model for code generation

    def generate(self, project_name: str, file_path: str, requirements: Dict[str, Any]) -> str:
        """Generate code for a specific file in the project."""
        logger.info(f"Generating code for {file_path} in project {project_name}")
        
        # Get the framework from requirements
        framework = requirements.get("suggested_frameworks", ["python"])[0]
        
        # Get relevant context from RAG system
        context = self.rag_system.query(
            f"{framework} {os.path.basename(file_path)} implementation",
            "code_examples"
        )
        
        # Get file description and project structure
        file_description = self._get_file_description(file_path, requirements)
        project_files = self.file_manager.list_project_files(project_name)
        project_structure = "\n".join([f"{f['path']}" for f in project_files])
        
        # Get related files content
        related_files = self._get_related_files_content(project_name, file_path)
        
        # Prepare the prompt for the LLM
        prompt = f"""
        Task: Generate production-ready code for {file_path} in a {framework} project.
        
        Project Details:
        1. Project Name: {project_name}
        2. File Description: {file_description}
        3. Framework: {framework}
        4. Project Type: {requirements.get('project_type', 'Unknown')}
        5. Features: {json.dumps(requirements.get('features', []))}
        6. Database Required: {requirements.get('database_required', False)}
        7. Database Type: {requirements.get('database_type', 'none')}
        8. Has Frontend: {requirements.get('has_frontend', False)}
        
        Project Structure:
        {project_structure}
        
        Related Files:
        {related_files}
        
        Context:
        {context}
        
        Requirements:
        1. Generate clean, optimized, production-ready code for {file_path}
        2. Follow best practices for {framework}
        3. Include necessary imports
        4. Add docstrings and comments
        5. Handle errors appropriately
        6. Ensure code is properly formatted
        7. Use type hints where applicable
        8. Follow PEP 8 style guide for Python files
        """
        
        # Generate code using the model
        response = self.model_manager.generate(prompt=prompt, model=self.model)
        
        # Clean the generated code
        ext = os.path.splitext(file_path)[1]
        cleaned_code = self._clean_code_response(response, ext)
        
        # Write the cleaned code to the file
        self.file_manager.write_file(project_name, file_path, cleaned_code)
        
        return cleaned_code

    def _get_file_description(self, file_path: str, requirements: Dict[str, Any]) -> str:
        """Get the description of the file from the requirements."""
        if "file_structure" in requirements:
            for item in requirements["file_structure"]:
                if item["path"] == file_path:
                    return item.get("description", "")
        
        # If not found, infer from filename
        filename = os.path.basename(file_path)
        descriptions = {
            "main.py": "Main application file",
            "app.py": "Main application file",
            "models.py": "Data models",
            "views.py": "View functions or classes",
            "urls.py": "URL routing configuration",
            "settings.py": "Application settings",
            "utils.py": "Utility functions",
            "forms.py": "Form definitions",
            "admin.py": "Admin interface configuration",
            "tests.py": "Test cases",
            "requirements.txt": "Project dependencies",
            "README.md": "Project documentation"
        }
        
        if filename in descriptions:
            return descriptions[filename]
        elif filename.endswith(".html"):
            return "HTML template"
        elif filename.endswith(".css"):
            return "CSS stylesheet"
        elif filename.endswith(".js"):
            return "JavaScript code"
        else:
            return f"Code file: {filename}"

    def _get_related_files_content(self, project_name: str, current_file_path: str) -> str:
        """Get the content of related files to provide context."""
        related_content = []
        current_dir = os.path.dirname(current_file_path)
        
        for file in self.file_manager.list_project_files(project_name):
            file_path = file["path"]
            if file_path == current_file_path:
                continue
                
            # Only include files in the same directory or parent directory
            file_dir = os.path.dirname(file_path)
            if file_dir != current_dir and not current_dir.startswith(file_dir):
                continue
                
            content = self.file_manager.read_file(project_name, file_path)
            if content:
                related_content.append(f"=== {file_path} ===\n{content}\n")
        
        # Limit the total size
        total_content = '\n'.join(related_content)
        if len(total_content) > 5000:
            return "Related files are too large to include in full. Please refer to the project structure."
        
        return total_content

    def _clean_code_response(self, response: str, ext: str) -> str:
        """Clean the code response from the model."""
        # Remove markdown code blocks
        code = response.strip()
        
        # Extract code from markdown code blocks if present
        if '```' in code:
            start_idx = code.find('```')
            end_idx = code.rfind('```')
            
            if start_idx != end_idx:
                # Extract the content between the first and last code block markers
                start_idx = code.find('\n', start_idx) + 1
                code = code[start_idx:end_idx].strip()
        
        # Remove common prefixes that might be explanations
        lines = code.split('\n')
        cleaned_lines = []
        for line in lines:
            # Skip lines that are likely explanations or comments outside the code
            if line.startswith(('Here', 'This', 'Now', 'Let', 'I', 'First', 'Next')) and not line.strip().startswith('#'):
                continue
            cleaned_lines.append(line)
        
        code = '\n'.join(cleaned_lines)
        
        return code
