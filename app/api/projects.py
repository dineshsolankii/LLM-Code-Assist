import os
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db, cache
from app.models.project import Project

logger = logging.getLogger(__name__)

projects_bp = Blueprint('projects', __name__, url_prefix='/api/project')


def _get_agents():
    """Lazy-load agents to avoid circular imports."""
    from utils.model_manager import ModelManager
    from utils.rag_system import RAGSystem
    from utils.file_manager import FileManager
    from agents.project_creator import ProjectCreator
    from agents.code_generator import CodeGenerator
    from agents.customizer import CodeCustomizer

    base_dir = current_app.config['PROJECTS_DIR']
    mm = ModelManager()
    rag = RAGSystem()
    fm = FileManager(base_dir)
    return {
        'model_manager': mm,
        'rag_system': rag,
        'file_manager': fm,
        'project_creator': ProjectCreator(mm, rag, fm),
        'code_generator': CodeGenerator(mm, rag, fm),
        'code_customizer': CodeCustomizer(mm, rag),
    }


@projects_bp.route('/create', methods=['POST'])
@login_required
def create_project():
    """Create a new project."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        project_name = data.get('projectName')
        framework = data.get('framework')
        analysis = data.get('analysis')

        if not all([project_name, framework, analysis]):
            missing = []
            if not project_name:
                missing.append('projectName')
            if not framework:
                missing.append('framework')
            if not analysis:
                missing.append('analysis')
            return jsonify({'success': False, 'error': f'Missing: {", ".join(missing)}'}), 400

        # Check duplicate
        existing = Project.query.filter_by(name=project_name, user_id=current_user.id).first()
        if existing:
            return jsonify({'success': False, 'error': 'Project with this name already exists'}), 409

        agents = _get_agents()

        # Create on filesystem
        project_path = agents['project_creator'].create_project(analysis, framework, project_name)

        # Generate code for main file
        main_file = 'app.py' if framework in ('flask', 'gradio', 'streamlit') else 'main.py'
        agents['code_generator'].generate(project_name, main_file, analysis)

        # Save to DB
        project = Project(
            name=project_name,
            description=analysis.get('description', ''),
            framework=framework,
            status='ready',
            user_id=current_user.id,
            analysis_data=analysis,
            requirements_text=data.get('requirements', ''),
            path=project_path,
        )
        db.session.add(project)
        db.session.commit()

        cache.delete(f'project_list_{current_user.id}')

        return jsonify({
            'success': True,
            'projectName': project_name,
            'path': project_path,
            'project': project.to_dict(),
        })

    except Exception as e:
        logger.error(f'Error creating project: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@projects_bp.route('', methods=['GET'])
@login_required
def list_projects():
    """List all projects for the current user."""
    try:
        # DB-backed listing
        db_projects = Project.query.filter_by(user_id=current_user.id).order_by(
            Project.created_at.desc()
        ).all()

        projects = [p.to_dict() for p in db_projects]

        # Also scan filesystem for legacy projects not yet in DB
        projects_dir = current_app.config['PROJECTS_DIR']
        db_names = {p['name'] for p in projects}

        if os.path.isdir(projects_dir):
            for name in os.listdir(projects_dir):
                path = os.path.join(projects_dir, name)
                if os.path.isdir(path) and name not in db_names:
                    created_at = datetime.fromtimestamp(os.path.getctime(path))
                    framework = 'python'
                    app_file = os.path.join(path, 'app.py')
                    if os.path.exists(app_file):
                        try:
                            with open(app_file, 'r') as f:
                                content = f.read()
                                if 'import gradio' in content or 'from gradio' in content:
                                    framework = 'gradio'
                        except Exception:
                            pass
                    projects.append({
                        'name': name,
                        'description': '',
                        'framework': framework,
                        'status': 'ready',
                        'created_at': created_at.isoformat(),
                        'updated_at': created_at.isoformat(),
                        'path': path,
                    })

        return jsonify({'success': True, 'projects': projects})

    except Exception as e:
        logger.error(f'Error listing projects: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@projects_bp.route('/<project_name>', methods=['DELETE'])
@login_required
def delete_project(project_name):
    """Delete a project."""
    try:
        if not project_name:
            return jsonify({'success': False, 'error': 'No project name'}), 400

        agents = _get_agents()
        agents['file_manager'].delete_project(project_name)

        # Remove from DB
        project = Project.query.filter_by(name=project_name, user_id=current_user.id).first()
        if project:
            db.session.delete(project)
            db.session.commit()

        cache.delete(f'project_list_{current_user.id}')

        return jsonify({'success': True})

    except Exception as e:
        logger.error(f'Error deleting project: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
