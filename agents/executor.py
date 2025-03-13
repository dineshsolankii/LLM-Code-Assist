#!/usr/bin/env python
import os
import subprocess
import logging
import signal
import sys
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

class ProjectExecutor:
    def __init__(self):
        self.running_processes = {}
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'projects')
    
    def execute(self, project_name: str, command: str = "run", output_callback: Optional[Callable[[str], None]] = None, stop_event=None) -> Dict[str, Any]:
        """Execute a command for the project."""
        project_path = os.path.join(self.base_dir, project_name)
        
        if not os.path.exists(project_path):
            raise FileNotFoundError(f"Project {project_name} not found")

        # Install dependencies first if running
        if command == "run":
            self._install_dependencies(project_path, output_callback)
            if stop_event and stop_event.is_set():
                return {"status": "stopped"}

        # Get command to run
        cmd_args = self._get_command_args(project_path, command)
        
        # Run the command
        return self._run_command(project_name, project_path, cmd_args, output_callback, stop_event)
    
    def _get_command_args(self, project_path: str, command: str) -> list:
        """Get command arguments based on project type."""
        # Check for Gradio project
        app_file = os.path.join(project_path, 'app.py')
        if os.path.exists(app_file):
            try:
                with open(app_file, 'r') as f:
                    content = f.read()
                    if 'import gradio' in content or 'from gradio' in content:
                        return ["python", "-u", "app.py"]  # -u for unbuffered output
            except:
                pass

        # Default to main.py for Python projects
        return ["python", "-u", "main.py"]  # -u for unbuffered output

    def _install_dependencies(self, project_path: str, output_callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """Install project dependencies."""
        req_file = os.path.join(project_path, 'requirements.txt')
        if not os.path.exists(req_file):
            return {"status": "no_requirements"}
            
        try:
            if output_callback:
                output_callback("Installing dependencies...")
            
            # Run pip install with subprocess.run for faster execution
            process = subprocess.Popen(
                ["pip", "install", "-r", "requirements.txt"],
                cwd=project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=dict(os.environ, PYTHONUNBUFFERED="1")
            )
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line and output_callback:
                    output_callback(line.strip())
            
            return {"status": "success" if process.returncode == 0 else "error"}
        except Exception as e:
            logger.error(f"Error installing dependencies: {str(e)}")
            if output_callback:
                output_callback(f"Error installing dependencies: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _run_command(self, project_name: str, project_path: str, cmd_args: list, 
                    output_callback: Optional[Callable[[str], None]] = None,
                    stop_event=None) -> Dict[str, Any]:
        """Run a command and handle its output."""
        try:
            # Kill any existing process
            if project_name in self.running_processes:
                try:
                    old_process = self.running_processes[project_name]
                    os.killpg(os.getpgid(old_process.pid), signal.SIGTERM)
                except:
                    pass
                del self.running_processes[project_name]
            
            # Start new process with optimized settings
            process = subprocess.Popen(
                cmd_args,
                cwd=project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True,
                preexec_fn=os.setsid,  # Create new process group
                env=dict(os.environ, PYTHONUNBUFFERED="1")  # Force Python to be unbuffered
            )
            
            self.running_processes[project_name] = process
            
            # Read output efficiently using select
            import select
            
            # Set stdout to non-blocking mode
            import fcntl
            import os
            
            fd = process.stdout.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            
            while True:
                # Check stop event first
                if stop_event and stop_event.is_set():
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    return {"status": "stopped"}
                
                # Use select to wait for output
                ready_to_read, _, _ = select.select([process.stdout], [], [], 0.1)
                
                if ready_to_read:
                    line = process.stdout.readline()
                    if line:
                        if output_callback:
                            output_callback(line.strip())
                    else:
                        # No more output
                        if process.poll() is not None:
                            break
                elif process.poll() is not None:
                    # Process finished
                    break
            
            return {
                "status": "success" if process.returncode == 0 else "error",
                "exit_code": process.returncode
            }
            
        except Exception as e:
            logger.error(f"Error running command: {str(e)}")
            if output_callback:
                output_callback(f"Error running command: {str(e)}")
            return {"status": "error", "error": str(e)}
        finally:
            if project_name in self.running_processes:
                del self.running_processes[project_name]
