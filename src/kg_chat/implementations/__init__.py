"""Implementations of the chatbot."""

from .duckdb_implementation import DuckDBImplementation
from .neo4j_implementation import Neo4jImplementation

__all__ = ["DuckDBImplementation", "Neo4jImplementation"]
