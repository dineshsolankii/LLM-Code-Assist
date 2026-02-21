#!/usr/bin/env python
import os
import json
import logging
from typing import Dict, Any
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class CodeGenerator(BaseAgent):
    def __init__(self, model_manager, rag_system, file_manager):
        super().__init__(model_manager, rag_system)
        self.file_manager = file_manager

    def generate(self, project_name, file_path, requirements):
        logger.info(f'Generating code for {file_path} in {project_name}')
        framework = requirements.get('suggested_frameworks', ['python'])[0]
        context = self.rag_system.query(f'{framework} {os.path.basename(file_path)} implementation', 'code_examples')
        file_desc = self._get_file_description(file_path, requirements)
        project_files = self.file_manager.list_project_files(project_name)
        structure = '\n'.join([f['path'] for f in project_files])
        related = self._get_related_files_content(project_name, file_path)

        prompt = f"""Generate production-ready code for {file_path} in a {framework} project.
        Project: {project_name} | File: {file_desc} | Type: {requirements.get('project_type','')}
        Features: {json.dumps(requirements.get('features', []))}
        DB: {requirements.get('database_required', False)} ({requirements.get('database_type','none')})
        Frontend: {requirements.get('has_frontend', False)}
        Structure:\n{structure}\nRelated:\n{related}\nContext:\n{context}
        Generate clean code with imports, docstrings, error handling, type hints."""
        response = self.model_manager.generate(prompt=prompt, model=self.model)
        ext = os.path.splitext(file_path)[1]
        cleaned = self._clean_code_response(response, ext)
        self.file_manager.write_file(project_name, file_path, cleaned)
        return cleaned

    def _get_file_description(self, file_path, requirements):
        if 'file_structure' in requirements:
            for item in requirements['file_structure']:
                if item.get('path') == file_path:
                    return item.get('description', '')
        descs = {'main.py': 'Main application', 'app.py': 'Main application', 'models.py': 'Data models', 'utils.py': 'Utilities'}
        return descs.get(os.path.basename(file_path), f'Code file: {os.path.basename(file_path)}')

    def _get_related_files_content(self, project_name, current_file_path):
        related = []
        current_dir = os.path.dirname(current_file_path)
        for f in self.file_manager.list_project_files(project_name):
            fp = f['path']
            if fp == current_file_path:
                continue
            file_dir = os.path.dirname(fp)
            if file_dir != current_dir and not current_dir.startswith(file_dir):
                continue
            content = self.file_manager.read_file(project_name, fp)
            if content:
                related.append(f'=== {fp} ===\n{content}\n')
        total = '\n'.join(related)
        return 'Related files too large.' if len(total) > 5000 else total

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
