import os
import logging
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required

logger = logging.getLogger(__name__)

files_bp = Blueprint('files', __name__, url_prefix='/api/project')


def _get_file_manager():
    from utils.file_manager import FileManager
    return FileManager(current_app.config['PROJECTS_DIR'])


@files_bp.route('/<project_name>/files', methods=['GET'])
@login_required
def list_project_files(project_name):
    """List all files in a project."""
    try:
        if not project_name:
            return jsonify({'success': False, 'error': 'No project name'}), 400

        fm = _get_file_manager()
        files = fm.list_project_files(project_name)
        return jsonify({'success': True, 'files': files})

    except Exception as e:
        logger.error(f'Error listing files: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@files_bp.route('/<project_name>/file', methods=['GET'])
@login_required
def get_file_content(project_name):
    """Get the content of a file."""
    try:
        file_path = request.args.get('path')
        if not all([project_name, file_path]):
            return jsonify({'success': False, 'error': 'Missing parameters'}), 400

        projects_dir = current_app.config['PROJECTS_DIR']
        abs_path = os.path.join(projects_dir, project_name, file_path)

        # Security: prevent path traversal
        abs_path = os.path.realpath(abs_path)
        if not abs_path.startswith(os.path.realpath(projects_dir)):
            return jsonify({'success': False, 'error': 'Invalid path'}), 403

        if not os.path.exists(abs_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404

        with open(abs_path, 'r') as f:
            content = f.read()

        return jsonify({'success': True, 'content': content})

    except Exception as e:
        logger.error(f'Error reading file: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@files_bp.route('/<project_name>/file', methods=['POST'])
@login_required
def save_file(project_name):
    """Save file content."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        file_path = data.get('path')
        content = data.get('content')

        if not all([project_name, file_path, content is not None]):
            return jsonify({'success': False, 'error': 'Missing fields'}), 400

        projects_dir = current_app.config['PROJECTS_DIR']
        abs_path = os.path.join(projects_dir, project_name, file_path)

        # Security: prevent path traversal
        abs_path = os.path.realpath(abs_path)
        if not abs_path.startswith(os.path.realpath(projects_dir)):
            return jsonify({'success': False, 'error': 'Invalid path'}), 403

        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w') as f:
            f.write(content)

        return jsonify({'success': True})

    except Exception as e:
        logger.error(f'Error saving file: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
