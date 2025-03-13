#!/usr/bin/env python
import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self, base_dir: str):
        """Initialize the file manager with a base directory."""
        self.base_dir = base_dir
        # Ensure the base directory exists and has proper permissions
        os.makedirs(base_dir, exist_ok=True)
        # Make sure we're not trying to use /project_root directly
        if self.base_dir == '/project_root':
            self.base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'projects')
            os.makedirs(self.base_dir, exist_ok=True)
        
    def get_project_path(self, project_name: str) -> str:
        """Get the absolute path for a project."""
        return os.path.join(self.base_dir, project_name)
        
    def create_project_structure(self, project_name: str, file_structure: List[Dict[str, str]]) -> None:
        """Create project directory structure from a list of files and directories."""
        project_path = self.get_project_path(project_name)
        os.makedirs(project_path, exist_ok=True)
        
        for item in file_structure:
            path = item["path"]
            item_type = item["type"]
            full_path = os.path.join(project_path, path)
            
            if item_type == "directory":
                os.makedirs(full_path, exist_ok=True)
                logger.info(f"Created directory: {full_path}")
            elif item_type == "file":
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                if not os.path.exists(full_path):
                    with open(full_path, 'w') as f:
                        f.write("")
                    logger.info(f"Created empty file: {full_path}")
                    
    def write_file(self, project_name: str, file_path: str, content: str) -> None:
        """Write content to a file in the project."""
        full_path = os.path.join(self.get_project_path(project_name), file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w') as f:
            f.write(content)
        logger.info(f"Wrote content to file: {full_path}")
        
    def read_file(self, project_name: str, file_path: str) -> Optional[str]:
        """Read content from a file in the project."""
        full_path = os.path.join(self.get_project_path(project_name), file_path)
        
        if not os.path.exists(full_path):
            logger.error(f"File not found: {full_path}")
            return None
            
        try:
            with open(full_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {full_path}: {str(e)}")
            return None
            
    def list_project_files(self, project_name: str) -> List[Dict[str, str]]:
        """List all files in a project."""
        project_path = self.get_project_path(project_name)
        if not os.path.exists(project_path):
            return []
            
        files = []
        for root, _, filenames in os.walk(project_path):
            for filename in sorted(filenames):
                if filename.startswith('.') or filename.endswith(('.pyc', '.pyo')):
                    continue
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, project_path)
                files.append({
                    "path": rel_path,
                    "name": filename,
                    "type": "file"
                })
        return files
        
    def delete_project(self, project_name: str) -> bool:
        """Delete a project directory."""
        project_path = self.get_project_path(project_name)
        if not os.path.exists(project_path):
            return False
            
        try:
            import shutil
            shutil.rmtree(project_path)
            logger.info(f"Deleted project: {project_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting project {project_path}: {str(e)}")
            return False
