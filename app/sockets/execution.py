import logging
from threading import Event, Thread
from flask import request
from app.extensions import socketio

logger = logging.getLogger(__name__)

# Store active sessions and their stop events
active_sessions = {}


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info(f'Client connected: {request.sid}')


@socketio.on('disconnect')
def handle_disconnect():
    """Clean up on client disconnect."""
    session_id = request.sid
    if session_id in active_sessions:
        active_sessions[session_id]['stop_event'].set()
        del active_sessions[session_id]
    logger.info(f'Client disconnected: {session_id}')


@socketio.on('execute')
def handle_execute_command(data):
    """Handle project execution via WebSocket."""
    from agents.executor import ProjectExecutor

    project_name = data.get('projectName')
    command = data.get('command', 'run')
    session_id = request.sid

    def output_callback(line):
        if line:
            socketio.emit('execution_output', {'output': line}, room=session_id)

    def run_command():
        try:
            stop_event = Event()
            active_sessions[session_id] = {'stop_event': stop_event}

            executor = ProjectExecutor()
            result = executor.execute(
                project_name,
                command,
                output_callback=output_callback,
                stop_event=stop_event,
            )

            if not stop_event.is_set():
                socketio.emit('execution_finished', {'success': True}, room=session_id)

        except Exception as e:
            logger.error(f'Execution error: {e}', exc_info=True)
            socketio.emit('execution_error', {'error': str(e)}, room=session_id)
        finally:
            if session_id in active_sessions:
                del active_sessions[session_id]

    Thread(target=run_command, daemon=True).start()
    return {'status': 'started', 'message': 'Project execution started'}


@socketio.on('stop_execution')
def handle_stop_execution():
    """Stop project execution."""
    session_id = request.sid
    if session_id in active_sessions:
        active_sessions[session_id]['stop_event'].set()
        socketio.emit('execution_stopped', room=session_id)
        logger.info(f'Execution stopped for session: {session_id}')
