import logging
from flask import request
from app.extensions import socketio

logger = logging.getLogger(__name__)


@socketio.on('analyze_requirements')
def handle_analyze_requirements(data):
    """Handle requirements analysis via WebSocket."""
    try:
        if not data:
            raise ValueError('No data provided')

        name = data.get('name')
        requirements = data.get('requirements')
        framework = data.get('framework')

        if not all([name, requirements, framework]):
            raise ValueError('Missing required fields: name, requirements, or framework')

        from utils.model_manager import ModelManager
        from utils.rag_system import RAGSystem
        from agents.requirement_analyzer import RequirementAnalyzer

        mm = ModelManager()
        rag = RAGSystem()
        analyzer = RequirementAnalyzer(mm, rag)
        analysis = analyzer.analyze(requirements)

        socketio.emit('analysis_result', {
            'success': True,
            'analysis': analysis,
        }, room=request.sid)

    except Exception as e:
        logger.error(f'Analysis error: {e}', exc_info=True)
        socketio.emit('analysis_error', {
            'success': False,
            'error': str(e),
        }, room=request.sid)
