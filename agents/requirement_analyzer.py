#!/usr/bin/env python
import json
import logging
import re
from typing import Dict, Any
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class RequirementAnalyzer(BaseAgent):
    def __init__(self, model_manager, rag_system):
        super().__init__(model_manager, rag_system)

    def analyze(self, user_prompt):
        logger.info(f'Analyzing requirements: {user_prompt[:100]}...')
        context = self.rag_system.query(f'project requirements for {user_prompt}', 'project_requirements')
        prompt = f"""
        Task: Analyze the following project requirements and extract structured information.

        User's Project Description:
        {user_prompt}

        Additional Context:
        {context}

        Return a JSON object with this structure:
        {{
            "project_type": "type description",
            "description": "detailed description",
            "features": [{{"name": "name", "description": "desc", "priority": "high|medium|low"}}],
            "database_required": true|false,
            "database_type": "sql|nosql|none",
            "has_frontend": true|false,
            "suggested_frameworks": ["framework1"],
            "suggested_packages": ["package1"],
            "file_structure": [{{"path": "path", "type": "file|directory", "description": "desc"}}]
        }}

        Return only valid JSON, no other text.
        """
        try:
            response = self.model_manager.generate(prompt=prompt, model=self.model)
            if isinstance(response, str):
                try:
                    json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
                    if json_match:
                        response = json_match.group(1)
                    requirements = json.loads(response)
                except json.JSONDecodeError:
                    requirements = {'components': ['Task Manager'], 'structure': ['CRUD']}
            elif isinstance(response, dict):
                requirements = response
            else:
                return self._get_default_requirements()
            return self._validate_requirements(requirements)
        except Exception as e:
            logger.error(f'Error analyzing requirements: {e}')
            return self._get_default_requirements()

    def _validate_requirements(self, req):
        for field in ['project_type', 'description', 'features', 'database_required', 'has_frontend', 'suggested_frameworks', 'suggested_packages']:
            if field not in req:
                if field in ('features', 'suggested_frameworks', 'suggested_packages'):
                    req[field] = []
                elif field in ('database_required', 'has_frontend'):
                    req[field] = False
                else:
                    req[field] = 'Not specified'
        if req.get('database_required') and 'database_type' not in req:
            req['database_type'] = 'sql'
        for f in req.get('features', []):
            if isinstance(f, dict):
                f.setdefault('name', 'Unnamed')
                f.setdefault('description', 'No description')
                f.setdefault('priority', 'medium')
        return req

    def _get_default_requirements(self):
        return {
            'project_type': 'web app', 'description': 'A simple calculator web application.',
            'features': [{'name': 'Basic arithmetic', 'description': 'Add, subtract, multiply, divide.', 'priority': 'high'}],
            'database_required': False, 'database_type': 'none', 'has_frontend': True,
            'suggested_frameworks': ['gradio'], 'suggested_packages': ['gradio>=4.0.0', 'numpy'],
            'file_structure': [
                {'path': 'app.py', 'type': 'file', 'description': 'Main application'},
                {'path': 'requirements.txt', 'type': 'file', 'description': 'Dependencies'},
                {'path': 'README.md', 'type': 'file', 'description': 'Documentation'},
            ],
        }
