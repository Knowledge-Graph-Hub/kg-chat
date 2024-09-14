"""A module for the schema of a knowledge graph."""

from typing import List

from pydantic import BaseModel


class Node(BaseModel):
    """A class to represent a node in a knowledge graph."""

    label: str
    id: str
    category: str

    def __repr__(self):
        """Return a string representation of the node."""
        return f"Node(label={self.label}, id={self.id}, category={self.category})"


class Edge(BaseModel):
    """A class to represent an edge in a knowledge graph."""

    subject: Node
    object: Node
    predicate: str

    def __repr__(self):
        """Return a string representation of the edge."""
        return f"Edge(subject={self.subject}, object={self.object}, predicate={self.predicate})"


class GraphSchema(BaseModel):
    """A class to represent the schema of a knowledge graph."""

    nodes: List[Node]
    edges: List[Edge]

    def to_dict(self):
        """Return the schema as a dictionary."""
        return self.dict()

    def to_json(self):
        """Return the schema as a JSON string."""
        return self.json(indent=4)

    def __repr__(self):
        """Return a string representation of the schema."""
        return f"GraphSchema(nodes={self.nodes}, edges={self.edges})"
