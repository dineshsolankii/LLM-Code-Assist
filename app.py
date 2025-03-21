from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
import logging
from datetime import datetime
import subprocess
from threading import Event, Thread
from queue import Queue

from agents.requirement_analyzer import RequirementAnalyzer
from agents.project_creator import ProjectCreator
from agents.code_generator import CodeGenerator
from agents.executor import ProjectExecutor
from agents.customizer import CodeCustomizer
from utils.model_manager import ModelManager
from utils.rag_system import RAGSystem
from utils.file_manager import FileManager

# Set tokenizers parallelism to avoid fork warnings
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
    static_folder='static',
    template_folder='templates'
)
CORS(app)

# Configure Flask app
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production
app.config['PROJECTS_DIR'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'projects')

# Ensure projects directory exists
os.makedirs(app.config['PROJECTS_DIR'], exist_ok=True)

# Initialize Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize agents
model_manager = ModelManager()
rag_system = RAGSystem()
file_manager = FileManager(app.config['PROJECTS_DIR'])
requirement_analyzer = RequirementAnalyzer(model_manager, rag_system)
project_creator = ProjectCreator(model_manager, rag_system, file_manager)
code_generator = CodeGenerator(model_manager, rag_system, file_manager)
project_executor = ProjectExecutor()
code_customizer = CodeCustomizer(model_manager, rag_system)

# Store active sessions and their stop events
active_sessions = {}

# Routes
@app.route('/')
def index():
    """Render the main application page."""
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files."""
    return send_from_directory('static', path)

# API Routes
@app.route('/api/analyze', methods=['POST'])
def analyze_requirements():
    """Analyze project requirements."""
    try:
        data = request.get_json()
        if not data or 'requirements' not in data:
            return jsonify({'success': False, 'error': 'No requirements provided'})
        
        requirements = data['requirements']
        analysis = requirement_analyzer.analyze(requirements)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
    except Exception as e:
        logger.error(f"Error analyzing requirements: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/frameworks', methods=['GET'])
def get_frameworks():
    """Get available frameworks."""
    try:
        frameworks = [
            {
                'id': 'python',
                'name': 'Python Script',
                'description': 'Create a simple Python script',
                'icon': 'fab fa-python'
            },
            {
                'id': 'gradio',
                'name': 'Gradio App',
                'description': 'Create a Gradio web application',
                'icon': 'fas fa-globe'
            }
        ]
        
        return jsonify({
            'success': True,
            'frameworks': frameworks
        })
    except Exception as e:
        logger.error(f"Error getting frameworks: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/project/create', methods=['POST'])
def create_project():
    """Create a new project."""
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data received in project creation request")
            return jsonify({'success': False, 'error': 'No data provided'})
            
        project_name = data.get('projectName')
        framework = data.get('framework')
        analysis = data.get('analysis')
        requirements = data.get('requirements')
        
        logger.info(f"Creating project: {project_name} with framework: {framework}")
        
        if not all([project_name, framework, analysis]):
            missing = []
            if not project_name: missing.append('projectName')
            if not framework: missing.append('framework')
            if not analysis: missing.append('analysis')
            error_msg = f"Missing required fields: {', '.join(missing)}"
            logger.error(error_msg)
            return jsonify({'success': False, 'error': error_msg})
        
        # Ensure file_structure exists in analysis
        if 'file_structure' not in analysis or not analysis['file_structure']:
            logger.info(f"No file structure found in analysis, generating one")
        
        # Create the project
        logger.info(f"Creating project structure for {project_name}")
        project_path = project_creator.create_project(analysis, framework, project_name)
        
        # Generate code for main.py or app.py
        main_file = "app.py" if framework in ["flask", "gradio", "streamlit"] else "main.py"
        logger.info(f"Generating code for {main_file}")
        code_generator.generate(project_name, main_file, analysis)
        
        logger.info(f"Project {project_name} created successfully at {project_path}")
        return jsonify({
            'success': True,
            'projectName': project_name,
            'path': project_path
        })
    except Exception as e:
        import traceback
        logger.error(f"Error creating project: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/project', methods=['GET'])
def list_projects():
    """List all projects."""
    try:
        projects_dir = app.config['PROJECTS_DIR']
        projects = []
        
        for name in os.listdir(projects_dir):
            path = os.path.join(projects_dir, name)
            if os.path.isdir(path):
                # Get project metadata
                created_at = datetime.fromtimestamp(os.path.getctime(path))
                description = ""
                framework = "python"  # Default framework
                
                # Try to determine framework from files
                if os.path.exists(os.path.join(path, 'app.py')):
                    with open(os.path.join(path, 'app.py'), 'r') as f:
                        content = f.read()
                        if 'import gradio' in content or 'from gradio' in content:
                            framework = 'gradio'
                
                projects.append({
                    'name': name,
                    'path': path,
                    'created_at': created_at.isoformat(),
                    'description': description,
                    'framework': framework
                })
        
        return jsonify({
            'success': True,
            'projects': sorted(projects, key=lambda x: x['created_at'], reverse=True)
        })
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/project/<project_name>/files', methods=['GET'])
def list_project_files(project_name):
    """List all files in a project."""
    try:
        if not project_name:
            return jsonify({'success': False, 'error': 'No project name provided'})
        
        # Get files from the file manager
        files = file_manager.list_project_files(project_name)
        
        return jsonify({
            'success': True,
            'files': files
        })
    except Exception as e:
        logger.error(f"Error listing project files: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/project/<project_name>/file', methods=['GET'])
def get_file_content(project_name):
    """Get the content of a file."""
    try:
        file_path = request.args.get('path')
        
        if not all([project_name, file_path]):
            return jsonify({'success': False, 'error': 'Missing required parameters'})
        
        # Get absolute path
        abs_path = os.path.join(app.config['PROJECTS_DIR'], project_name, file_path)
        
        # Ensure file exists and is within project directory
        if not os.path.exists(abs_path) or not abs_path.startswith(app.config['PROJECTS_DIR']):
            return jsonify({'success': False, 'error': 'File not found'})
        
        # Read file content
        with open(abs_path, 'r') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'content': content
        })
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/project/<project_name>/file', methods=['POST'])
def save_file(project_name):
    """Save file content."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'})
        
        file_path = data.get('path')
        content = data.get('content')
        
        if not all([project_name, file_path, content is not None]):
            return jsonify({'success': False, 'error': 'Missing required fields'})
        
        # Get absolute path
        abs_path = os.path.join(app.config['PROJECTS_DIR'], project_name, file_path)
        
        # Ensure path is within project directory
        if not abs_path.startswith(app.config['PROJECTS_DIR']):
            return jsonify({'success': False, 'error': 'Invalid file path'})
        
        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        
        # Write file content
        with open(abs_path, 'w') as f:
            f.write(content)
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/customize-code', methods=['POST'])
def customize_code():
    """Customize code based on user request."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'})
        
        current_code = data.get('currentCode')
        customization_request = data.get('customizationRequest')
        
        if not all([current_code, customization_request]):
            return jsonify({'success': False, 'error': 'Missing required fields'})
        
        # Customize code
        customized_code = code_customizer.customize(current_code, customization_request)
        
        return jsonify({
            'success': True,
            'code': customized_code
        })
    except Exception as e:
        logger.error(f"Error customizing code: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Clean up on client disconnect."""
    session_id = request.sid
    if session_id in active_sessions:
        active_sessions[session_id]['stop_event'].set()
        del active_sessions[session_id]
    logger.info(f"Client disconnected: {session_id}")

@socketio.on('analyze_requirements')
def handle_analyze_requirements(data):
    """Handle requirements analysis via WebSocket."""
    try:
        logger.info(f"Analyzing requirements for session: {request.sid}")
        
        # Validate input data
        if not data:
            raise ValueError('No data provided')
            
        name = data.get('name')
        requirements = data.get('requirements')
        framework = data.get('framework')
        
        if not all([name, requirements, framework]):
            raise ValueError('Missing required fields: name, requirements, or framework')
        
        # Analyze requirements
        analysis = requirement_analyzer.analyze(requirements)
        
        # Emit result back to client
        emit('analysis_result', {
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error analyzing requirements: {error_msg}")
        emit('analysis_error', {
            'success': False,
            'error': error_msg
        })

@socketio.on('execute')
def handle_execute_command(data):
    """Handle project execution via WebSocket."""
    project_name = data.get('projectName')
    command = data.get('command', 'run')
    session_id = request.sid
    
    def output_callback(line):
        if line:
            socketio.emit('output', {'line': line}, room=session_id)
    
    def run_command():
        try:
            # Create event for this session
            stop_event = Event()
            active_sessions[session_id] = {
                'stop_event': stop_event
            }
            
            # Execute the project
            result = project_executor.execute(
                project_name, 
                command,
                output_callback=output_callback,
                stop_event=stop_event
            )
            
            if not stop_event.is_set():
                socketio.emit('execution_finished', {'success': True}, room=session_id)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error executing command: {error_msg}")
            socketio.emit('execution_error', {'error': error_msg}, room=session_id)
        finally:
            if session_id in active_sessions:
                del active_sessions[session_id]
    
    # Start execution in a daemon thread
    Thread(target=run_command, daemon=True).start()
    return {'status': 'started', 'message': 'Project execution started'}

@socketio.on('stop_execution')
def handle_stop_execution():
    """Stop project execution."""
    session_id = request.sid
    if session_id in active_sessions:
        active_sessions[session_id]['stop_event'].set()
        socketio.emit('execution_stopped', room=session_id)
        logger.info(f"Execution stopped for session: {session_id}")

@app.route('/api/project/<project_name>', methods=['DELETE'])
def delete_project(project_name):
    """Delete a project."""
    try:
        if not project_name:
            return jsonify({'success': False, 'error': 'No project name provided'})
        
        # Delete the project using file manager
        success = file_manager.delete_project(project_name)
        
        if not success:
            return jsonify({'success': False, 'error': 'Project not found or could not be deleted'})
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8001, debug=True)
