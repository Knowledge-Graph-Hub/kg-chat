"""Tests for Neo4jImplementation class."""

import os
from unittest.mock import MagicMock, patch

import pytest
from kg_chat.implementations import Neo4jImplementation

# Define the condition to skip tests
skip_neo4j_tests = pytest.mark.skipif(
    os.getenv("SKIP_NEO4J_TESTS") == "true", reason="Skipping Neo4j tests in GitHub Actions"
)


@pytest.fixture
@patch("neo4j.GraphDatabase.driver")
@patch("langchain_community.graphs.Neo4jGraph")
@patch("langchain_openai.ChatOpenAI")
@patch("langchain_community.chains.graph_qa.cypher.GraphCypherQAChain.from_llm")
def neo4j_impl(mock_from_llm, mock_chat_openai, mock_neo4j_graph, mock_driver):
    """Fixture to initialize Neo4jImplementation with mocks."""
    # Mock the return values for the constructor dependencies
    mock_driver.return_value = MagicMock()
    mock_neo4j_graph.return_value = MagicMock()
    mock_chat_openai.return_value = MagicMock()
    mock_from_llm.return_value = MagicMock()

    return Neo4jImplementation()


@skip_neo4j_tests
def test_toggle_safe_mode(neo4j_impl):
    """Test toggling safe mode on and off."""
    neo4j_impl.toggle_safe_mode(False)
    assert not neo4j_impl.safe_mode
    neo4j_impl.toggle_safe_mode(True)
    assert neo4j_impl.safe_mode


@skip_neo4j_tests
def test_is_safe_command(neo4j_impl):
    """Test checking if a command is safe to execute."""
    assert neo4j_impl.is_safe_command("MATCH (n) RETURN n")
    assert not neo4j_impl.is_safe_command("CREATE (n:Node {id: '1'})")


@skip_neo4j_tests
@patch("neo4j.GraphDatabase.driver")
def test_execute_query(mock_driver):
    """Test executing a query in safe mode."""
    mock_session = MagicMock()
    mock_transaction = MagicMock()
    mock_driver.return_value.session.return_value.__enter__.return_value = mock_session
    mock_session.read_transaction.return_value = mock_transaction
    neo4j_impl = Neo4jImplementation()
    query = "MATCH (n) RETURN n"
    result = neo4j_impl.execute_query(query)

    mock_session.read_transaction.assert_called_once()
    assert result == mock_transaction


@skip_neo4j_tests
@patch("neo4j.GraphDatabase.driver")
def test_execute_query_unsafe(mock_driver, neo4j_impl):
    """Test executing a query in unsafe mode."""
    neo4j_impl.safe_mode = True
    query = "CREATE (n:Node {id: '1'})"
    with pytest.raises(ValueError):
        neo4j_impl.execute_query(query)


@skip_neo4j_tests
@patch("langchain_community.graphs.Neo4jGraph.query")
def test_execute_query_using_langchain(mock_query, neo4j_impl):
    """Test executing a query using Langchain."""
    query = "MATCH (n) RETURN n"
    mock_query.return_value = "result"
    result = neo4j_impl.execute_query_using_langchain(query)
    mock_query.assert_called_once_with(query)
    assert result == "result"


@skip_neo4j_tests
@patch("neo4j.GraphDatabase.driver")
def test_clear_database(mock_driver):
    """Test clearing the database."""
    mock_session = MagicMock()
    mock_driver.return_value.session.return_value.__enter__.return_value = mock_session
    neo4j_impl = Neo4jImplementation()
    neo4j_impl.clear_database()
    mock_session.write_transaction.assert_called_once()


@skip_neo4j_tests
@patch("neo4j.GraphDatabase.driver")
def test_ensure_index(mock_driver):
    """Test ensuring that the index on :Node(id) exists."""
    mock_session = MagicMock()
    mock_driver.return_value.session.return_value.__enter__.return_value = mock_session
    neo4j_impl = Neo4jImplementation()
    neo4j_impl.ensure_index()
    mock_session.write_transaction.assert_called_once()


# TODO
# @skip_neo4j_tests
# @patch('langchain.chains.base.Chain.invoke')
# def test_get_human_response(mock_invoke, neo4j_impl):
#     query = "MATCH (n) RETURN n"
#     mock_invoke.return_value = {"result": "response"}
#     result = neo4j_impl.get_human_response(query)
#     mock_invoke.assert_called_once_with({"query": query})
#     assert result == "response"

# @skip_neo4j_tests
# @patch('langchain.chains.base.Chain.invoke')
# def test_get_structured_response(mock_invoke, neo4j_impl):
#     query = "Get all nodes"
#     structured_query_result = structure_query(query)
#     mock_invoke.return_value = {"result": "response"}
#     result = neo4j_impl.get_structured_response(query)
#     mock_invoke.assert_called_once_with({"query": structured_query_result})
#     assert result == "response"


@skip_neo4j_tests
@patch("neo4j.GraphDatabase.driver")
def test_create_nodes(mock_driver):
    """Test creating nodes in the database."""
    mock_session = MagicMock()
    mock_driver.return_value.session.return_value.__enter__.return_value = mock_session
    nodes = [{"id": "1", "category": "Person", "label": "John"}]
    neo4j_impl = Neo4jImplementation()
    neo4j_impl.create_nodes(nodes)
    mock_session.write_transaction.assert_called_once()


@skip_neo4j_tests
@patch("neo4j.GraphDatabase.driver")
def test_create_edges(mock_driver):
    """Test creating edges in the database."""
    mock_session = MagicMock()
    mock_driver.return_value.session.return_value.__enter__.return_value = mock_session
    edges = [{"subject": "1", "predicate": "KNOWS", "object": "2"}]
    neo4j_impl = Neo4jImplementation()
    neo4j_impl.create_edges(edges)
    mock_session.write_transaction.assert_called_once()


@skip_neo4j_tests
@patch("neo4j.GraphDatabase.driver")
def test_show_schema(mock_driver):
    """Test showing the schema of the database."""
    mock_session = MagicMock()
    mock_driver.return_value.session.return_value.__enter__.return_value = mock_session
    mock_transaction = MagicMock()
    mock_session.read_transaction.return_value = mock_transaction
    neo4j_impl = Neo4jImplementation()
    neo4j_impl.show_schema()
    mock_session.read_transaction.assert_called_once()


# TODO
# @skip_neo4j_tests
# @patch('kg_chat.implementations.Neo4jImplementation.clear_database')
# @patch('kg_chat.implementations.Neo4jImplementation.ensure_index')
# @patch('kg_chat.implementations.Neo4jImplementation.create_nodes')
# @patch('kg_chat.implementations.Neo4jImplementation.create_edges')
# def test_load_kg(mock_create_edges, mock_create_nodes, mock_ensure_index, mock_clear_database, neo4j_impl):
#     data_dir = TESTS_INPUT_DIR  # Replace with actual path
#     nodes_filepath = data_dir / "nodes.tsv"
#     edges_filepath = data_dir / "edges.tsv"

#     with patch('builtins.open', new_callable=MagicMock) as mock_open:
#         mock_open.side_effect = [
#             MagicMock(),  # For nodes file
#             MagicMock()   # For edges file
#         ]
#         neo4j_impl.load_kg(data_dir=data_dir, block_size=1000)

#     mock_clear_database.assert_called_once()
#     mock_ensure_index.assert_called_once()
#     mock_create_nodes.assert_called()
#     mock_create_edges.assert_called()
