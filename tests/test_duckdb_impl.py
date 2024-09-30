"""Tests for DuckDBImplementation class."""

from unittest.mock import MagicMock

import pytest
from sqlalchemy import text

from kg_chat.constants import TESTS_INPUT_DIR
from kg_chat.implementations import DuckDBImplementation
from kg_chat.utils import get_llm_config

LLM_CONFIG = get_llm_config("openai")


@pytest.fixture
def db_impl():
    """Fixture to initialize DuckDBImplementation."""
    mock_connect = MagicMock()
    db_instance = DuckDBImplementation(data_dir=TESTS_INPUT_DIR, llm_config=LLM_CONFIG)
    db_instance.conn = mock_connect
    return db_instance


# TODO
# def test_init(mocker):
#     mock_connect = mocker.patch('duckdb.connect', return_value=MagicMock())
#     db_impl = DuckDBImplementation(data_dir=TESTS_INPUT_DIR, llm_config=LLM_CONFIG)
#     assert db_impl.safe_mode is True
#     assert db_impl.conn is not None
#     assert db_impl.llm is not None
#     assert db_impl.engine is not None
#     assert db_impl.db is not None
#     assert db_impl.toolkit is not None
#     assert db_impl.agent is not None


def test_toggle_safe_mode(db_impl):
    """Test toggling safe mode on and off."""
    db_impl.toggle_safe_mode(False)
    assert db_impl.safe_mode is False
    db_impl.toggle_safe_mode(True)
    assert db_impl.safe_mode is True


def test_is_safe_command(db_impl):
    """Test checking if a command is safe to execute."""
    safe_query = "SELECT * FROM nodes"
    unsafe_query = "DROP TABLE nodes"
    assert db_impl.is_safe_command(safe_query) is True
    assert db_impl.is_safe_command(unsafe_query) is False


def test_execute_query_safe_mode(db_impl):
    """Test executing a query in safe mode."""
    # Define a safe query
    query = "SELECT * FROM nodes"

    # Mock the execute method to return a controlled response
    mock_result = []
    db_impl.conn.execute.return_value.fetchall.return_value = mock_result

    # Execute the query using the db_impl instance
    result = db_impl.execute_query(query)

    # Assert that execute was called with the correct query
    executed_query = db_impl.conn.execute.call_args[0][0]
    assert str(executed_query) == str(text(query))

    # Assert that the result matches the mock result
    assert result == mock_result


def test_execute_query_unsafe_mode(db_impl):
    """Test executing an unsafe query raises ValueError."""
    # Enable safe mode
    db_impl.safe_mode = True

    # Define an unsafe query (assuming is_safe_command will return False)
    query = "DROP TABLE nodes"

    # Mock the is_safe_command method to return False
    db_impl.is_safe_command = MagicMock(return_value=False)

    # Execute the query and expect a ValueError
    with pytest.raises(ValueError, match=f"Unsafe command detected: {query}"):
        db_impl.execute_query(query)


def test_execute_query_unsafe_command_in_safe_mode(db_impl):
    """Test executing an unsafe command in safe mode."""
    query = "DROP TABLE nodes"
    with pytest.raises(ValueError):
        db_impl.execute_query(query)


def test_clear_database(mocker, db_impl):
    """Test clearing the database."""
    # Patch the execute method of the connection object
    mock_execute = mocker.patch.object(db_impl.conn, "execute")

    # Mock the execute_unsafe_operation to call the provided function immediately
    mocker.patch.object(db_impl, "execute_unsafe_operation", side_effect=lambda func: func())

    # Call the method to clear the database
    db_impl.clear_database()

    # Define the expected SQL queries as strings
    expected_queries = ["DROP TABLE IF EXISTS edges", "DROP TABLE IF EXISTS nodes"]

    # Extract the actual SQL queries from the mock calls
    actual_queries = [call.args[0].text for call in mock_execute.mock_calls]

    # Print the actual queries for debugging purposes
    print(actual_queries)

    # Assert that the actual queries match the expected queries in any order
    assert sorted(actual_queries) == sorted(expected_queries)


def test_get_human_response(mocker, db_impl):
    """Test getting a human response from the database."""
    mock_invoke = mocker.patch("langchain.chains.base.Chain.invoke", return_value={"output": "response"})
    mock_invoke.return_value = {"output": "response"}
    prompt = "What is the capital of France?"
    response = db_impl.get_human_response(prompt)
    mock_invoke.assert_called_once_with(
        {
            "input": prompt,
            "tools": db_impl.tools,
            "tool_names": db_impl.tool_names,
        }
    )
    assert response == "response"


def test_get_structured_response(mocker, db_impl):
    """Test getting a structured response from the database."""
    mock_structure_query = mocker.patch("kg_chat.utils.structure_query")
    mock_invoke = mocker.patch("langchain.chains.base.Chain.invoke", return_value={"output": "response"})
    mock_structure_query.return_value = "structured query"
    mock_invoke.return_value = {"output": "response"}
    prompt = "Get all nodes"
    response = db_impl.get_structured_response(prompt)
    # TODO mock_structure_query.assert_called_once_with(prompt)
    mock_invoke.assert_called_once_with(
        {
            "input": prompt,
            "tools": db_impl.tools,
            "tool_names": db_impl.tool_names,
        }
    )
    assert response == "response"


def test_create_edges(mocker, db_impl):
    """Test creating edges in the database."""
    # Patch the execute method of the DuckDBPyConnection object
    mock_execute = mocker.patch.object(db_impl.conn, "execute")

    # Define the edges to be inserted
    edges = [("subject1", "predicate1", "object1"), ("subject2", "predicate2", "object2")]

    # Call the method to create edges
    db_impl.create_edges(edges)

    # Define the expected SQL query as a string
    expected_query = "INSERT INTO edges (subject, predicate, object) VALUES (?, ?, ?)"

    # Check if execute was called once with all edges or multiple times
    if mock_execute.call_count == 1:
        # Extract the actual call arguments
        actual_query, actual_edges = mock_execute.call_args[0]

        # Assert that the actual query matches the expected query
        assert str(actual_query) == expected_query

        # Assert that the edges were passed correctly
        assert actual_edges == edges
    else:
        # Assert that execute was called for each edge
        assert mock_execute.call_count == len(edges)

        # Extract the actual call arguments
        actual_calls = mock_execute.call_args_list

        # Assert that each call has the correct query and parameters
        for i, edge in enumerate(edges):
            actual_query, actual_params = actual_calls[i][0]
            assert str(actual_query) == expected_query
            assert actual_params == edge


def test_create_nodes(mocker, db_impl):
    """Test creating nodes in the database."""
    # Patch the execute method of the DuckDBPyConnection object
    mock_execute = mocker.patch.object(db_impl.conn, "execute")

    # Define the nodes to be inserted
    nodes = [("id1", "category1", "label1"), ("id2", "category2", "label2")]

    # Call the method to create nodes
    db_impl.create_nodes(nodes)

    # Define the expected SQL query as a string
    expected_query = "INSERT INTO nodes (id, category, label) VALUES (?, ?, ?)"

    # Check if execute was called once with all nodes or multiple times
    if mock_execute.call_count == 1:
        # Extract the actual call arguments
        actual_query, actual_nodes = mock_execute.call_args[0]

        # Assert that the actual query matches the expected query
        assert str(actual_query) == expected_query

        # Assert that the nodes were passed correctly
        assert actual_nodes == nodes
    else:
        # Assert that execute was called for each node
        assert mock_execute.call_count == len(nodes)

        # Extract the actual call arguments
        actual_calls = mock_execute.call_args_list

        # Assert that each call has the correct query and parameters
        for i, node in enumerate(nodes):
            actual_query, actual_params = actual_calls[i][0]
            assert str(actual_query) == expected_query
            assert actual_params == node


def test_show_schema(mocker, db_impl):
    """Test showing the schema of the database."""
    # Patch the execute method of the DuckDBPyConnection object
    mock_execute = mocker.patch.object(db_impl.conn, "execute")

    # Mock the return value of fetchall
    mock_execute.return_value.fetchall.return_value = [("nodes",), ("edges",)]

    # Call the method to show the schema
    result = db_impl.show_schema()

    # Define the expected SQL query as a TextClause object
    expected_query = text("PRAGMA show_tables")

    # Assert that execute was called once with the correct arguments
    assert mock_execute.call_count == 1
    actual_query = mock_execute.call_args[0][0]

    # Compare the compiled SQL strings
    assert str(actual_query) == str(expected_query)

    # Assert that the result is None (since pprint returns None)
    assert result is None


def test_execute_query_using_langchain(mocker, db_impl):
    """Test executing a query using the langchain agent."""
    mock_invoke = mocker.patch("langchain.chains.base.Chain.invoke", return_value={"output": "response"})
    mock_invoke.return_value = {"output": "response"}
    prompt = "Get all nodes"
    response = db_impl.execute_query_using_langchain(prompt)
    mock_invoke.assert_called_once_with(
        {
            "input": prompt,
            "tools": db_impl.tools,
            "tool_names": db_impl.tool_names,
        }
    )
    assert response == "response"
