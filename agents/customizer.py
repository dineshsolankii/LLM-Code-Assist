#!/usr/bin/env python
"""Code customizer agent - FIXED: method signature for backward compatibility."""
import os
import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class CodeCustomizer(BaseAgent):
    def __init__(self, model_manager, rag_system):
        super().__init__(model_manager, rag_system)

    def customize(self, project_name='', file_path='', current_code='', customization_request=''):
        """Customize existing code. All params optional for backward compat."""
        logger.info(f'Customizing code for {file_path or "inline"} in {project_name or "unknown"}')
        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'projects')
        project_structure = ''
        if project_name:
            project_path = os.path.join(base_dir, project_name)
            if os.path.isdir(project_path):
                project_structure = self._get_project_structure(project_path)
        context = self.rag_system.query(
            f'{customization_request} {os.path.basename(file_path) if file_path else "code"}', 'code_examples',
        )
        prompt = f"""Task: Customize the following code based on the user's request.
        File: {file_path or 'inline'}
        Project: {project_name or 'unknown'}
        User's Request: {customization_request}
        Current Code:
        ```
        {current_code}
        ```
        {f'Project Structure:{chr(10)}{project_structure}' if project_structure else ''}
        Reference: {context}
        Instructions:
        1. Analyze code structure
        2. Implement changes preserving structure
        3. Clean, optimized code with best practices
        4. Update imports as needed
        5. Return complete modified code
        Modified Code:"""
        response = self.model_manager.generate(prompt=prompt, model=self.model)
        ext = os.path.splitext(file_path)[1] if file_path else '.py'
        modified = self._clean_code_response(response, ext)
        if project_name and file_path:
            full_path = os.path.join(base_dir, project_name, file_path)
            if os.path.isdir(os.path.dirname(full_path)):
                try:
                    with open(full_path, 'w') as f:
                        f.write(modified)
                except Exception as e:
                    logger.error(f'Error writing customized code: {e}')
        return modified

    def _get_project_structure(self, project_path):
        structure = []
        for root, dirs, files in os.walk(project_path):
            level = root.replace(project_path, '').count(os.sep)
            indent = '    ' * level
            rel = os.path.relpath(root, project_path)
            if rel != '.':
                structure.append(f'{indent}{os.path.basename(root)}/')
            sub_indent = '    ' * (level + 1)
            for f in files:
                structure.append(f'{sub_indent}{f}')
        return '\n'.join(structure)

    def _clean_code_response(self, response, ext):
        if isinstance(response, dict):
            return str(response)
        code = response.strip()
        if '```' in code:
            start = code.find('```')
            end = code.rfind('```')
            if start != end:
                start = code.find('\n', start) + 1
                code = code[start:end].strip()
        lines = code.split('\n')
        cleaned = [l for l in lines if not (l.startswith(('Here', 'This', 'Now', 'Let', 'I', 'First', 'Next')) and not l.strip().startswith('#'))]
        return '\n'.join(cleaned)
