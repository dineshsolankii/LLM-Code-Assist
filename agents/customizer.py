#!/usr/bin/env python
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CodeCustomizer:
    def __init__(self, model_manager, rag_system):
        self.model_manager = model_manager
        self.rag_system = rag_system
        self.model = "qwen2.5-coder:7b"  # Using the 16B model for code customization

    def customize(self, project_name: str, file_path: str, current_code: str, customization_request: str) -> str:
        """
        Customize existing code based on user request.
        
        Args:
            project_name: The name of the project
            file_path: The path to the file within the project
            current_code: The current code content
            customization_request: The user's request for customization
            
        Returns:
            The customized code
        """
        logger.info(f"Customizing code for {file_path} in project {project_name}")
        
        # Get the base directory for projects
        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'projects')
        project_path = os.path.join(base_dir, project_name)
        
        # Get the full path to the file
        full_path = os.path.join(project_path, file_path)
        
        # Get the file extension
        _, ext = os.path.splitext(file_path)
        
        # Get relevant context from RAG system
        context = self.rag_system.query(
            f"{customization_request} {os.path.basename(file_path)}",
            "code_examples"
        )
        
        # Get project structure for context
        project_structure = self._get_project_structure(project_path)
        
        # Prepare the prompt for the LLM
        prompt = f"""
        Task: Customize the following code based on the user's request.
        
        File: {file_path}
        Project: {project_name}
        
        User's Customization Request:
        {customization_request}
        
        Current Code:
        ```
        {current_code}
        ```
        
        Project Structure:
        {project_structure}
        
        Reference Examples:
        {context}
        
        Instructions:
        1. Carefully analyze the current code and understand its structure and functionality
        2. Implement the requested changes while preserving the overall structure and style
        3. Ensure the modified code is clean, optimized, and follows best practices
        4. Add or modify comments as needed to explain the changes
        5. Maintain consistent formatting and indentation
        6. Ensure all imports are properly updated
        7. Return the complete modified code, not just the changed parts
        
        Modified Code:
        """
        
        # Get response from the model
        response = self.model_manager.generate(self.model, prompt)
        
        # Clean the response
        modified_code = self._clean_code_response(response, ext)
        
        # Write the modified code to the file
        with open(full_path, 'w') as f:
            f.write(modified_code)
        
        logger.info(f"Customized code for {file_path}")
        
        return modified_code

    def _get_project_structure(self, project_path: str) -> str:
        """Get a string representation of the project structure."""
        structure = []
        
        for root, dirs, files in os.walk(project_path):
            level = root.replace(project_path, '').count(os.sep)
            indent = ' ' * 4 * level
            rel_path = os.path.relpath(root, project_path)
            if rel_path != '.':
                structure.append(f"{indent}{os.path.basename(root)}/")
            
            sub_indent = ' ' * 4 * (level + 1)
            for file in files:
                structure.append(f"{sub_indent}{file}")
        
        return '\n'.join(structure)

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
