"""Base agent class providing shared model management."""
import logging

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for all AI agents."""

    def __init__(self, model_manager, rag_system):
        self.model_manager = model_manager
        self.rag_system = rag_system

    @property
    def model(self):
        """Always use the dynamically selected active model."""
        return self.model_manager.active_model
