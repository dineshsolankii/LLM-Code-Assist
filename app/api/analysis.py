import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.chat_history import ChatHistory

logger = logging.getLogger(__name__)

analysis_bp = Blueprint('analysis', __name__, url_prefix='/api')


def _get_analyzer():
    from utils.model_manager import ModelManager
    from utils.rag_system import RAGSystem
    from agents.requirement_analyzer import RequirementAnalyzer
    mm = ModelManager()
    rag = RAGSystem()
    return RequirementAnalyzer(mm, rag)


@analysis_bp.route('/analyze', methods=['POST'])
@login_required
def analyze_requirements():
    """Analyze project requirements."""
    try:
        data = request.get_json()
        if not data or 'requirements' not in data:
            return jsonify({'success': False, 'error': 'No requirements provided'}), 400

        requirements = data['requirements']

        # Save user message to chat history
        chat_entry = ChatHistory(
            user_id=current_user.id,
            role='user',
            message=requirements,
            message_type='requirements',
        )
        db.session.add(chat_entry)
        db.session.commit()

        analyzer = _get_analyzer()
        analysis = analyzer.analyze(requirements)

        # Save assistant response
        import json
        assistant_entry = ChatHistory(
            user_id=current_user.id,
            role='assistant',
            message=json.dumps(analysis),
            message_type='requirements',
        )
        db.session.add(assistant_entry)
        db.session.commit()

        return jsonify({'success': True, 'analysis': analysis})

    except Exception as e:
        logger.error(f'Error analyzing requirements: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@analysis_bp.route('/customize-code', methods=['POST'])
@login_required
def customize_code():
    """Customize code based on user request."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        current_code = data.get('currentCode')
        customization_request = data.get('customizationRequest')
        project_name = data.get('projectName', '')
        file_path = data.get('filePath', '')

        if not all([current_code, customization_request]):
            return jsonify({'success': False, 'error': 'Missing fields'}), 400

        from utils.model_manager import ModelManager
        from utils.rag_system import RAGSystem
        from agents.customizer import CodeCustomizer

        mm = ModelManager()
        rag = RAGSystem()
        customizer = CodeCustomizer(mm, rag)
        customized_code = customizer.customize(
            project_name=project_name,
            file_path=file_path,
            current_code=current_code,
            customization_request=customization_request,
        )

        return jsonify({'success': True, 'code': customized_code})

    except Exception as e:
        logger.error(f'Error customizing code: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
