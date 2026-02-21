"""Project business logic layer."""
import os
import logging
from app.extensions import db
from app.models.project import Project

logger = logging.getLogger(__name__)


def create_project_record(name, description, framework, user_id, analysis_data, requirements_text, path):
    """Create a project record in the database."""
    project = Project(
        name=name,
        description=description,
        framework=framework,
        status='ready',
        user_id=user_id,
        analysis_data=analysis_data,
        requirements_text=requirements_text,
        path=path,
    )
    db.session.add(project)
    db.session.commit()
    return project


def get_user_projects(user_id):
    """Get all projects for a user."""
    return Project.query.filter_by(user_id=user_id).order_by(
        Project.created_at.desc()
    ).all()


def get_project(name, user_id):
    """Get a specific project by name and user."""
    return Project.query.filter_by(name=name, user_id=user_id).first()


def delete_project_record(name, user_id):
    """Delete a project from the database."""
    project = get_project(name, user_id)
    if project:
        db.session.delete(project)
        db.session.commit()
        return True
    return False


def update_project_status(name, user_id, status):
    """Update project status."""
    project = get_project(name, user_id)
    if project:
        project.status = status
        db.session.commit()
    return project
