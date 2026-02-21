from flask import Blueprint, render_template, jsonify, current_app
from flask_login import current_user

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Render the main application page."""
    if current_app.config.get('SKIP_AUTH') or current_user.is_authenticated:
        return render_template('index.html')
    return render_template('login.html')


@main_bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'service': 'llm-code-assist'})


@main_bp.route('/api/frameworks', methods=['GET'])
def get_frameworks():
    """Get available frameworks for project generation."""
    frameworks = [
        # ── Python / Backend ──────────────────────────────────────────────
        {
            'id': 'python',
            'name': 'Python Script',
            'description': 'Standalone Python script with virtual environment',
            'icon': 'fab fa-python',
            'color': '#3b82f6',
            'type': 'backend',
        },
        {
            'id': 'flask',
            'name': 'Flask',
            'description': 'Lightweight Python web framework with REST API',
            'icon': 'fas fa-flask',
            'color': '#6366f1',
            'type': 'backend',
        },
        {
            'id': 'fastapi',
            'name': 'FastAPI',
            'description': 'High-performance async Python API with OpenAPI docs',
            'icon': 'fas fa-bolt',
            'color': '#10b981',
            'type': 'backend',
        },
        {
            'id': 'django',
            'name': 'Django',
            'description': 'Full-featured Python web framework with ORM & admin',
            'icon': 'fas fa-leaf',
            'color': '#22c55e',
            'type': 'backend',
        },
        # ── Frontend / JavaScript ─────────────────────────────────────────
        {
            'id': 'react',
            'name': 'React',
            'description': 'Component-based UI library with hooks and JSX',
            'icon': 'fab fa-react',
            'color': '#06b6d4',
            'type': 'frontend',
        },
        {
            'id': 'nextjs',
            'name': 'Next.js',
            'description': 'React framework with SSR, routing, and API routes',
            'icon': 'fas fa-layer-group',
            'color': '#f8fafc',
            'type': 'fullstack',
        },
        {
            'id': 'vue',
            'name': 'Vue.js',
            'description': 'Progressive JavaScript framework with reactive data',
            'icon': 'fab fa-vuejs',
            'color': '#4ade80',
            'type': 'frontend',
        },
        {
            'id': 'express',
            'name': 'Express.js',
            'description': 'Minimal Node.js web framework for REST APIs',
            'icon': 'fab fa-node-js',
            'color': '#f59e0b',
            'type': 'backend',
        },
        # ── Data / ML ─────────────────────────────────────────────────────
        {
            'id': 'gradio',
            'name': 'Gradio',
            'description': 'ML model demos with auto-generated web UI',
            'icon': 'fas fa-brain',
            'color': '#f97316',
            'type': 'ml',
        },
        {
            'id': 'streamlit',
            'name': 'Streamlit',
            'description': 'Data apps and dashboards in pure Python',
            'icon': 'fas fa-chart-bar',
            'color': '#ef4444',
            'type': 'ml',
        },
    ]
    return jsonify({'success': True, 'frameworks': frameworks})


@main_bp.route('/api/model', methods=['GET'])
def get_active_model():
    """Get the currently active Ollama model."""
    try:
        from utils.model_manager import ModelManager
        mm = ModelManager()
        return jsonify({'success': True, 'model': mm.active_model or 'Not loaded'})
    except Exception as e:
        return jsonify({'success': False, 'model': 'Unknown', 'error': str(e)})
