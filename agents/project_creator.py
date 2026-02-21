#!/usr/bin/env python
import os
import json
import logging
from typing import Dict, Any, List
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

# Frameworks that use Node.js / npm instead of Python / pip
NODE_FRAMEWORKS = {'react', 'nextjs', 'vue', 'express'}

# Default file structures per framework
DEFAULT_STRUCTURES: Dict[str, List[Dict]] = {
    'python': [
        {'path': 'main.py',           'type': 'file',      'description': 'Main entry point'},
        {'path': 'requirements.txt',  'type': 'file',      'description': 'Python dependencies'},
        {'path': 'README.md',         'type': 'file',      'description': 'Project documentation'},
        {'path': 'src',               'type': 'directory', 'description': 'Source code'},
        {'path': 'src/__init__.py',   'type': 'file',      'description': 'Package init'},
        {'path': 'tests',             'type': 'directory', 'description': 'Unit tests'},
        {'path': 'tests/test_main.py','type': 'file',      'description': 'Main tests'},
    ],
    'flask': [
        {'path': 'app.py',            'type': 'file',      'description': 'Flask application factory'},
        {'path': 'requirements.txt',  'type': 'file',      'description': 'Python dependencies'},
        {'path': 'README.md',         'type': 'file',      'description': 'Project documentation'},
        {'path': 'templates',         'type': 'directory', 'description': 'Jinja2 templates'},
        {'path': 'templates/index.html','type': 'file',    'description': 'Main template'},
        {'path': 'static',            'type': 'directory', 'description': 'Static assets'},
        {'path': 'static/css',        'type': 'directory', 'description': 'Stylesheets'},
        {'path': 'static/js',         'type': 'directory', 'description': 'JavaScript files'},
        {'path': 'models.py',         'type': 'file',      'description': 'Database models'},
        {'path': 'routes.py',         'type': 'file',      'description': 'URL routes'},
        {'path': 'config.py',         'type': 'file',      'description': 'App configuration'},
    ],
    'fastapi': [
        {'path': 'main.py',           'type': 'file',      'description': 'FastAPI app entry point'},
        {'path': 'requirements.txt',  'type': 'file',      'description': 'Python dependencies'},
        {'path': 'README.md',         'type': 'file',      'description': 'Project documentation'},
        {'path': 'routers',           'type': 'directory', 'description': 'API routers'},
        {'path': 'routers/__init__.py','type': 'file',     'description': 'Routers package'},
        {'path': 'routers/api.py',    'type': 'file',      'description': 'API endpoints'},
        {'path': 'models',            'type': 'directory', 'description': 'SQLAlchemy models'},
        {'path': 'models/__init__.py','type': 'file',      'description': 'Models package'},
        {'path': 'schemas',           'type': 'directory', 'description': 'Pydantic schemas'},
        {'path': 'schemas/__init__.py','type': 'file',     'description': 'Schemas package'},
        {'path': 'database.py',       'type': 'file',      'description': 'DB session & engine'},
        {'path': 'config.py',         'type': 'file',      'description': 'Settings (pydantic-settings)'},
    ],
    'django': [
        {'path': 'manage.py',               'type': 'file',      'description': 'Django management CLI'},
        {'path': 'requirements.txt',        'type': 'file',      'description': 'Python dependencies'},
        {'path': 'README.md',               'type': 'file',      'description': 'Project documentation'},
        {'path': 'project',                 'type': 'directory', 'description': 'Django project package'},
        {'path': 'project/__init__.py',     'type': 'file',      'description': 'Project package init'},
        {'path': 'project/settings.py',     'type': 'file',      'description': 'Django settings'},
        {'path': 'project/urls.py',         'type': 'file',      'description': 'Root URL config'},
        {'path': 'project/wsgi.py',         'type': 'file',      'description': 'WSGI entry point'},
        {'path': 'app',                     'type': 'directory', 'description': 'Main Django app'},
        {'path': 'app/__init__.py',         'type': 'file',      'description': 'App package init'},
        {'path': 'app/models.py',           'type': 'file',      'description': 'Database models'},
        {'path': 'app/views.py',            'type': 'file',      'description': 'View functions'},
        {'path': 'app/urls.py',             'type': 'file',      'description': 'App URL routes'},
        {'path': 'app/admin.py',            'type': 'file',      'description': 'Admin panel config'},
        {'path': 'templates',               'type': 'directory', 'description': 'Django templates'},
        {'path': 'templates/index.html',    'type': 'file',      'description': 'Base template'},
        {'path': 'static',                  'type': 'directory', 'description': 'Static files'},
    ],
    'react': [
        {'path': 'package.json',              'type': 'file',      'description': 'npm dependencies & scripts'},
        {'path': 'README.md',                 'type': 'file',      'description': 'Project documentation'},
        {'path': '.gitignore',                'type': 'file',      'description': 'Git ignore rules'},
        {'path': 'public',                    'type': 'directory', 'description': 'Static public assets'},
        {'path': 'public/index.html',         'type': 'file',      'description': 'HTML entry point'},
        {'path': 'public/favicon.ico',        'type': 'file',      'description': 'Favicon'},
        {'path': 'src',                       'type': 'directory', 'description': 'React source code'},
        {'path': 'src/index.jsx',             'type': 'file',      'description': 'React DOM entry point'},
        {'path': 'src/App.jsx',               'type': 'file',      'description': 'Root App component'},
        {'path': 'src/App.css',               'type': 'file',      'description': 'App-level styles'},
        {'path': 'src/components',            'type': 'directory', 'description': 'Reusable components'},
        {'path': 'src/components/.gitkeep',   'type': 'file',      'description': 'Keep dir in git'},
        {'path': 'src/hooks',                 'type': 'directory', 'description': 'Custom React hooks'},
        {'path': 'src/pages',                 'type': 'directory', 'description': 'Page components'},
        {'path': 'src/utils',                 'type': 'directory', 'description': 'Utility functions'},
        {'path': 'src/styles',                'type': 'directory', 'description': 'Global styles'},
    ],
    'nextjs': [
        {'path': 'package.json',          'type': 'file',      'description': 'npm dependencies & scripts'},
        {'path': 'next.config.js',        'type': 'file',      'description': 'Next.js configuration'},
        {'path': 'README.md',             'type': 'file',      'description': 'Project documentation'},
        {'path': '.gitignore',            'type': 'file',      'description': 'Git ignore rules'},
        {'path': 'pages',                 'type': 'directory', 'description': 'File-based routing pages'},
        {'path': 'pages/index.jsx',       'type': 'file',      'description': 'Home page'},
        {'path': 'pages/_app.jsx',        'type': 'file',      'description': 'App wrapper'},
        {'path': 'pages/_document.jsx',   'type': 'file',      'description': 'HTML document'},
        {'path': 'pages/api',             'type': 'directory', 'description': 'API route handlers'},
        {'path': 'pages/api/hello.js',    'type': 'file',      'description': 'Example API route'},
        {'path': 'components',            'type': 'directory', 'description': 'Shared UI components'},
        {'path': 'components/Layout.jsx', 'type': 'file',      'description': 'Page layout wrapper'},
        {'path': 'styles',                'type': 'directory', 'description': 'CSS modules & globals'},
        {'path': 'styles/globals.css',    'type': 'file',      'description': 'Global stylesheet'},
        {'path': 'lib',                   'type': 'directory', 'description': 'Shared utilities & helpers'},
        {'path': 'public',                'type': 'directory', 'description': 'Static assets'},
    ],
    'vue': [
        {'path': 'package.json',          'type': 'file',      'description': 'npm dependencies & scripts'},
        {'path': 'vite.config.js',        'type': 'file',      'description': 'Vite build configuration'},
        {'path': 'README.md',             'type': 'file',      'description': 'Project documentation'},
        {'path': '.gitignore',            'type': 'file',      'description': 'Git ignore rules'},
        {'path': 'index.html',            'type': 'file',      'description': 'HTML entry point'},
        {'path': 'src',                   'type': 'directory', 'description': 'Vue source code'},
        {'path': 'src/main.js',           'type': 'file',      'description': 'Vue app entry point'},
        {'path': 'src/App.vue',           'type': 'file',      'description': 'Root App component'},
        {'path': 'src/components',        'type': 'directory', 'description': 'Vue components'},
        {'path': 'src/views',             'type': 'directory', 'description': 'Page view components'},
        {'path': 'src/router',            'type': 'directory', 'description': 'Vue Router config'},
        {'path': 'src/router/index.js',   'type': 'file',      'description': 'Router definition'},
        {'path': 'src/stores',            'type': 'directory', 'description': 'Pinia state stores'},
        {'path': 'src/assets',            'type': 'directory', 'description': 'Static assets'},
        {'path': 'public',                'type': 'directory', 'description': 'Public static files'},
    ],
    'express': [
        {'path': 'package.json',          'type': 'file',      'description': 'npm dependencies & scripts'},
        {'path': 'server.js',             'type': 'file',      'description': 'Express app entry point'},
        {'path': 'README.md',             'type': 'file',      'description': 'Project documentation'},
        {'path': '.gitignore',            'type': 'file',      'description': 'Git ignore rules'},
        {'path': '.env.example',          'type': 'file',      'description': 'Environment variable template'},
        {'path': 'routes',                'type': 'directory', 'description': 'Express route handlers'},
        {'path': 'routes/index.js',       'type': 'file',      'description': 'Root router'},
        {'path': 'routes/api.js',         'type': 'file',      'description': 'API routes'},
        {'path': 'middleware',            'type': 'directory', 'description': 'Custom middleware'},
        {'path': 'middleware/auth.js',    'type': 'file',      'description': 'Auth middleware'},
        {'path': 'controllers',           'type': 'directory', 'description': 'Route controller logic'},
        {'path': 'models',                'type': 'directory', 'description': 'Data models / schemas'},
        {'path': 'config',                'type': 'directory', 'description': 'App configuration'},
        {'path': 'config/database.js',    'type': 'file',      'description': 'DB connection config'},
    ],
    'gradio': [
        {'path': 'app.py',                'type': 'file',      'description': 'Gradio app entry point'},
        {'path': 'requirements.txt',      'type': 'file',      'description': 'Python dependencies'},
        {'path': 'README.md',             'type': 'file',      'description': 'Project documentation'},
        {'path': 'src',                   'type': 'directory', 'description': 'Source code'},
        {'path': 'src/__init__.py',       'type': 'file',      'description': 'Package init'},
        {'path': 'src/model.py',          'type': 'file',      'description': 'Model implementation'},
    ],
    'streamlit': [
        {'path': 'app.py',                'type': 'file',      'description': 'Streamlit app entry point'},
        {'path': 'requirements.txt',      'type': 'file',      'description': 'Python dependencies'},
        {'path': 'README.md',             'type': 'file',      'description': 'Project documentation'},
        {'path': 'pages',                 'type': 'directory', 'description': 'Multi-page app pages'},
        {'path': 'components',            'type': 'directory', 'description': 'Reusable UI components'},
        {'path': 'utils',                 'type': 'directory', 'description': 'Helper utilities'},
        {'path': 'data',                  'type': 'directory', 'description': 'Sample data files'},
    ],
}

# Default pip dependencies per framework
PIP_DEPS: Dict[str, List[str]] = {
    'flask':   ['flask>=3.0', 'flask-cors', 'python-dotenv'],
    'fastapi': ['fastapi>=0.100', 'uvicorn[standard]', 'pydantic>=2.0', 'python-dotenv'],
    'django':  ['django>=4.2', 'djangorestframework', 'python-dotenv'],
    'gradio':  ['gradio>=4.0.0', 'numpy', 'pillow'],
    'streamlit': ['streamlit>=1.30', 'pandas', 'numpy'],
}

# Default npm dependencies per framework
NPM_DEPS: Dict[str, Dict] = {
    'react': {
        'dependencies': {'react': '^18.2.0', 'react-dom': '^18.2.0'},
        'devDependencies': {
            'vite': '^5.0.0',
            '@vitejs/plugin-react': '^4.0.0',
        },
        'scripts': {
            'dev': 'vite',
            'build': 'vite build',
            'preview': 'vite preview',
        },
    },
    'nextjs': {
        'dependencies': {'next': '^14.0.0', 'react': '^18.2.0', 'react-dom': '^18.2.0'},
        'devDependencies': {},
        'scripts': {
            'dev': 'next dev',
            'build': 'next build',
            'start': 'next start',
            'lint': 'next lint',
        },
    },
    'vue': {
        'dependencies': {'vue': '^3.3.0', 'vue-router': '^4.2.0', 'pinia': '^2.1.0'},
        'devDependencies': {
            'vite': '^5.0.0',
            '@vitejs/plugin-vue': '^4.0.0',
        },
        'scripts': {
            'dev': 'vite',
            'build': 'vite build',
            'preview': 'vite preview',
        },
    },
    'express': {
        'dependencies': {
            'express': '^4.18.0',
            'dotenv': '^16.0.0',
            'cors': '^2.8.5',
            'helmet': '^7.0.0',
        },
        'devDependencies': {
            'nodemon': '^3.0.0',
        },
        'scripts': {
            'start': 'node server.js',
            'dev': 'nodemon server.js',
        },
    },
}


class ProjectCreator(BaseAgent):
    def __init__(self, model_manager, rag_system, file_manager):
        super().__init__(model_manager, rag_system)
        self.file_manager = file_manager

    def create_project(self, requirements, framework, project_name):
        try:
            logger.info(f'Creating project {project_name} with {framework}')
            if not project_name or not isinstance(project_name, str):
                raise ValueError(f'Invalid project name: {project_name}')
            if not framework or not isinstance(framework, str):
                raise ValueError(f'Invalid framework: {framework}')
            if not requirements or not isinstance(requirements, dict):
                raise ValueError('Invalid requirements')
            if 'file_structure' not in requirements or not requirements['file_structure']:
                requirements['file_structure'] = self._generate_file_structure(requirements, framework)
            if not isinstance(requirements['file_structure'], list):
                requirements['file_structure'] = []
            self.file_manager.create_project_structure(project_name, requirements['file_structure'])
            if framework in NODE_FRAMEWORKS:
                self._create_package_json(project_name, requirements, framework)
            else:
                self._create_requirements_file(project_name, requirements, framework)
            self._create_readme_file(project_name, requirements, framework)
            project_path = self.file_manager.get_project_path(project_name)
            logger.info(f'Project {project_name} created at {project_path}')
            return project_path
        except Exception as e:
            logger.error(f'Error creating project {project_name}: {e}', exc_info=True)
            raise

    def _generate_file_structure(self, requirements, framework):
        context = self.rag_system.query(
            f"project structure for {framework} {requirements.get('project_type', '')}",
            'project_structure'
        )
        prompt = f"""Generate a file structure for a {framework} project.
Project Type: {requirements.get('project_type', '')}
Features: {json.dumps(requirements.get('features', []))}
Database: {requirements.get('database_required', False)}
Frontend: {requirements.get('has_frontend', False)}
Context: {context}
Return JSON array: [{{"path": "path", "type": "file|directory", "description": "desc"}}]
Return ONLY valid JSON."""
        response = self.model_manager.generate(prompt=prompt, model=self.model)
        try:
            text = str(response).strip().replace('```json', '').replace('```', '').strip()
            file_structure = json.loads(text)
            for item in file_structure:
                if 'path' not in item or 'type' not in item:
                    raise KeyError(f'Missing field: {item}')
                item.setdefault('description', f"{item['type']} for the project")
            return file_structure
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f'Error parsing LLM file structure: {e}')
            return self._get_default_file_structure(framework)

    def _get_default_file_structure(self, framework: str) -> List[Dict]:
        return DEFAULT_STRUCTURES.get(framework, DEFAULT_STRUCTURES['python'])

    def _create_package_json(self, project_name, requirements, framework):
        """Write package.json for Node.js-based frameworks."""
        npm = NPM_DEPS.get(framework, {})
        pkg = {
            'name': project_name.lower().replace(' ', '-'),
            'version': '0.1.0',
            'private': True,
            'description': requirements.get('description', ''),
            'scripts': npm.get('scripts', {'start': 'node index.js'}),
            'dependencies': npm.get('dependencies', {}),
            'devDependencies': npm.get('devDependencies', {}),
        }
        # Merge any extra packages suggested by the LLM
        extra = requirements.get('suggested_packages', [])
        for pkg_spec in extra:
            if isinstance(pkg_spec, str) and not pkg_spec.startswith('-'):
                name = pkg_spec.split('>=')[0].split('==')[0].strip()
                pkg['dependencies'][name] = 'latest'
        self.file_manager.write_file(project_name, 'package.json', json.dumps(pkg, indent=2))

    def _create_requirements_file(self, project_name, requirements, framework):
        """Write requirements.txt for Python-based frameworks."""
        deps = ['pytest']
        deps.extend(PIP_DEPS.get(framework, []))
        if isinstance(requirements.get('suggested_packages'), list):
            deps.extend(requirements['suggested_packages'])
        self.file_manager.write_file(
            project_name, 'requirements.txt', '\n'.join(sorted(set(deps)))
        )

    def _create_readme_file(self, project_name, requirements, framework):
        features = requirements.get('features', [])
        features_str = ''
        for f in features:
            if isinstance(f, str):
                features_str += f'- {f}\n'
            elif isinstance(f, dict) and 'name' in f:
                desc = f.get('description', '')
                features_str += f"- **{f['name']}**: {desc}\n" if desc else f"- {f['name']}\n"
        if not features_str:
            features_str = '- No specific features listed'

        if framework in NODE_FRAMEWORKS:
            setup_cmd = 'npm install'
            run_cmd = 'npm run dev'
        elif framework in ('gradio', 'flask', 'streamlit'):
            setup_cmd = 'pip install -r requirements.txt'
            run_cmd = 'python app.py'
        elif framework == 'fastapi':
            setup_cmd = 'pip install -r requirements.txt'
            run_cmd = 'uvicorn main:app --reload'
        elif framework == 'django':
            setup_cmd = 'pip install -r requirements.txt'
            run_cmd = 'python manage.py runserver'
        else:
            setup_cmd = 'pip install -r requirements.txt'
            run_cmd = 'python main.py'

        content = f"""# {project_name}

{requirements.get('project_type', 'Project')}

## Description
{requirements.get('description', '')}

## Features
{features_str}
## Setup
```bash
{setup_cmd}
```

## Run
```bash
{run_cmd}
```

## Framework
{framework}
"""
        self.file_manager.write_file(project_name, 'README.md', content)
