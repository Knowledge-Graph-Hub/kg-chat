"""Interface for the Database."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class DatabaseInterface(ABC):
    """Interface for the Database."""

    @abstractmethod
    def execute_query(self, query: str) -> Any:
        """Execute a query against the database."""
        pass

    @abstractmethod
    def execute_query_using_langchain(self, query: str) -> str:
        """Execute a query against the database using Langchain."""
        pass

    @abstractmethod
    def load_kg(self):
        """Load the Knowledge Graph into the database."""
        pass

    @abstractmethod
    def show_schema(self) -> str:
        """Show the schema of the database."""
        pass

    @abstractmethod
    def get_human_response(self, query: str) -> str:
        """Get a human response from the database."""
        pass

    @abstractmethod
    def get_structured_response(self, query: str) -> str:
        """Get a structured response from the database."""
        pass

    @abstractmethod
    def clear_database(self):
        """Clear the database."""
        pass

    @abstractmethod
    def create_nodes(self, nodes: List[Dict[str, Any]]):
        """Create nodes in the database."""
        pass

    @abstractmethod
    def create_edges(self, edges: List[Dict[str, Any]]):
        """Create edges in the database."""
        pass

    @abstractmethod
    def toggle_safe_mode(self, enabled: bool):
        """Toggle safe mode on or off."""
        pass

    @abstractmethod
    def is_safe_command(self, command: str) -> bool:
        """Check if a command is safe to execute."""
        pass

    @abstractmethod
    def execute_unsafe_operation(self, operation: callable):
        """Execute an unsafe operation with safety measures."""
        pass
