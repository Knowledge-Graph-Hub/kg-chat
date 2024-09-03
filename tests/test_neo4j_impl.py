"""Tests for Neo4jImplementation class."""

from unittest.mock import MagicMock, patch

import pytest

from kg_chat.constants import TESTS_INPUT_DIR
from kg_chat.implementations import Neo4jImplementation
from kg_chat.utils import get_llm_config

LLM_CONFIG = get_llm_config("openai")


@pytest.fixture
@patch("neo4j.GraphDatabase.driver")
@patch("langchain_community.graphs.Neo4jGraph")
def neo4j_impl(mock_neo4j_graph, mock_driver):
    """Fixture to initialize Neo4jImplementation with mocks."""
    mock_neo4j_graph.return_value = MagicMock()
    mock_driver.return_value = MagicMock()
    return Neo4jImplementation(data_dir=TESTS_INPUT_DIR, llm_config=LLM_CONFIG)


def test_toggle_safe_mode(neo4j_impl):
    """
    Test toggling safe mode on and off.

    This test ensures that the `toggle_safe_mode` method correctly updates the
    `safe_mode` attribute of the `Neo4jImplementation` instance.
    """
    neo4j_impl.toggle_safe_mode(False)
    assert not neo4j_impl.safe_mode
    neo4j_impl.toggle_safe_mode(True)
    assert neo4j_impl.safe_mode


def test_is_safe_command(neo4j_impl):
    """
    Test checking if a command is safe to execute.

    This test verifies that the `is_safe_command` method correctly identifies
    safe and unsafe Cypher commands.
    """
    assert neo4j_impl.is_safe_command("MATCH (n) RETURN n")
    assert not neo4j_impl.is_safe_command("CREATE (n:Node {id: '1'})")


@patch("neo4j.GraphDatabase.driver")
def test_execute_query(mock_driver):
    """
    Test executing a query in safe mode.

    This test checks that the `execute_query` method correctly executes a read
    transaction when the query is safe.
    """
    mock_session = MagicMock()
    mock_transaction = MagicMock()
    mock_driver.return_value.session.return_value.__enter__.return_value = mock_session
    mock_session.read_transaction.return_value = mock_transaction
    neo4j_impl = Neo4jImplementation(data_dir=TESTS_INPUT_DIR, llm_config=LLM_CONFIG)
    query = "MATCH (n) RETURN n"
    result = neo4j_impl.execute_query(query)

    mock_session.read_transaction.assert_called_once()
    assert result == mock_transaction


@patch("neo4j.GraphDatabase.driver")
def test_execute_query_unsafe(mock_driver, neo4j_impl):
    """
    Test executing a query in unsafe mode.

    This test ensures that the `execute_query` method raises a ValueError when
    attempting to execute an unsafe query while in safe mode.
    """
    neo4j_impl.safe_mode = True
    query = "CREATE (n:Node {id: '1'})"
    with pytest.raises(ValueError):
        neo4j_impl.execute_query(query)


@patch("langchain_community.graphs.Neo4jGraph.query")
def test_execute_query_using_langchain(mock_query, neo4j_impl):
    """
    Test executing a query using Langchain.

    This test verifies that the `execute_query_using_langchain` method correctly
    delegates the query execution to the Langchain library.
    """
    query = "MATCH (n) RETURN n"
    mock_query.return_value = "result"
    result = neo4j_impl.execute_query_using_langchain(query)
    mock_query.assert_called_once_with(query)
    assert result == "result"


@patch("neo4j.GraphDatabase.driver")
def test_clear_database(mock_driver):
    """
    Test clearing the database.

    This test checks that the `clear_database` method correctly initiates a write
    transaction to clear all nodes and relationships in the database.
    """
    mock_session = MagicMock()
    mock_driver.return_value.session.return_value.__enter__.return_value = mock_session
    neo4j_impl = Neo4jImplementation(data_dir=TESTS_INPUT_DIR, llm_config=LLM_CONFIG)
    neo4j_impl.clear_database()
    mock_session.write_transaction.assert_called_once()


@patch("neo4j.GraphDatabase.driver")
def test_ensure_index(mock_driver):
    """
    Test ensuring that the index on :Node(id) exists.

    This test verifies that the `ensure_index` method correctly initiates a write
    transaction to create an index on the `id` property of `Node` labels.
    """
    mock_session = MagicMock()
    mock_driver.return_value.session.return_value.__enter__.return_value = mock_session
    neo4j_impl = Neo4jImplementation(data_dir=TESTS_INPUT_DIR, llm_config=LLM_CONFIG)
    neo4j_impl.ensure_index()
    mock_session.write_transaction.assert_called_once()


# TODO
# @patch('langchain.chains.base.Chain.invoke')
# def test_get_human_response(mock_invoke, neo4j_impl):
#     """
#     Test getting a human-readable response.
#
#     This test checks that the `get_human_response` method correctly invokes the
#     Langchain chain to get a human-readable response for a given query.
#     """
#     query = "MATCH (n) RETURN n"
#     mock_invoke.return_value = {"result": "response"}
#     result = neo4j_impl.get_human_response(query)
#     mock_invoke.assert_called_once_with({"query": query})
#     assert result == "response"

# @patch('langchain.chains.base.Chain.invoke')
# def test_get_structured_response(mock_invoke, neo4j_impl):
#     """
#     Test getting a structured response.
#
#     This test verifies that the `get_structured_response` method correctly invokes
#     the Langchain chain to get a structured response for a given query.
#     """
#     query = "Get all nodes"
#     structured_query_result = structure_query(query)
#     mock_invoke.return_value = {"result": "response"}
#     result = neo4j_impl.get_structured_response(query)
#     mock_invoke.assert_called_once_with({"query": structured_query_result})
#     assert result == "response"


@patch("neo4j.GraphDatabase.driver")
def test_create_nodes(mock_driver):
    """
    Test creating nodes in the database.

    This test checks that the `create_nodes` method correctly initiates a write
    transaction to create nodes in the database.
    """
    mock_session = MagicMock()
    mock_driver.return_value.session.return_value.__enter__.return_value = mock_session
    nodes = [{"id": "1", "category": "Person", "label": "John"}]
    neo4j_impl = Neo4jImplementation(data_dir=TESTS_INPUT_DIR, llm_config=LLM_CONFIG)
    neo4j_impl.create_nodes(nodes)
    mock_session.write_transaction.assert_called_once()


@patch("neo4j.GraphDatabase.driver")
def test_create_edges(mock_driver):
    """
    Test creating edges in the database.

    This test verifies that the `create_edges` method correctly initiates a write
    transaction to create relationships between nodes in the database.
    """
    mock_session = MagicMock()
    mock_driver.return_value.session.return_value.__enter__.return_value = mock_session
    edges = [{"subject": "1", "predicate": "KNOWS", "object": "2"}]
    neo4j_impl = Neo4jImplementation(data_dir=TESTS_INPUT_DIR, llm_config=LLM_CONFIG)
    neo4j_impl.create_edges(edges)
    mock_session.write_transaction.assert_called_once()


@patch("neo4j.GraphDatabase.driver")
def test_show_schema(mock_driver):
    """
    Test showing the schema of the database.

    This test checks that the `show_schema` method correctly initiates a read
    transaction to retrieve and display the schema of the database.
    """
    mock_session = MagicMock()
    mock_driver.return_value.session.return_value.__enter__.return_value = mock_session
    mock_transaction = MagicMock()
    mock_session.read_transaction.return_value = mock_transaction
    neo4j_impl = Neo4jImplementation(data_dir=TESTS_INPUT_DIR, llm_config=LLM_CONFIG)
    neo4j_impl.show_schema()
    mock_session.read_transaction.assert_called_once()


# TODO
# @patch('kg_chat.implementations.Neo4jImplementation.clear_database')
# @patch('kg_chat.implementations.Neo4jImplementation.ensure_index')
# @patch('kg_chat.implementations.Neo4jImplementation.create_nodes')
# @patch('kg_chat.implementations.Neo4jImplementation.create_edges')
# def test_load_kg(mock_create_edges, mock_create_nodes, mock_ensure_index, mock_clear_database, neo4j_impl):
#     """
#     Test loading a knowledge graph.
#
#     This test verifies that the `load_kg` method correctly loads nodes and edges
#     from files into the database, ensuring the database is cleared and indexed
#     before loading.
#     """
#     data_dir = TESTS_INPUT_DIR  # Replace with actual path
#     nodes_filepath = data_dir / "nodes.tsv"
#     edges_filepath = data_dir / "edges
