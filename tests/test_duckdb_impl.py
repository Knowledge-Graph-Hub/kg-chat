"""Tests for DuckDBImplementation class."""

from unittest.mock import call

import pytest
from kg_chat.implementations import DuckDBImplementation


@pytest.fixture
def db_impl():
    """Fixture to initialize DuckDBImplementation."""
    return DuckDBImplementation()


# TODO
# def test_init(mocker):
#     mock_connect = mocker.patch('duckdb.connect', return_value=MagicMock())
#     db_impl = DuckDBImplementation()
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


def test_execute_query_safe_mode(mocker, db_impl):
    """Test executing a query in safe mode."""
    mock_execute = mocker.patch("duckdb.DuckDBPyConnection.execute")
    mock_execute.return_value.fetchall.return_value = []
    query = "SELECT * FROM nodes"
    result = db_impl.execute_query(query)
    mock_execute.assert_called_once_with(query)
    assert result == []


def test_execute_query_unsafe_mode(mocker, db_impl):
    """Test executing a query in unsafe mode."""
    db_impl.safe_mode = False
    mock_execute = mocker.patch("duckdb.DuckDBPyConnection.execute")
    mock_execute.return_value.fetchall.return_value = []
    query = "DROP TABLE nodes"
    result = db_impl.execute_query(query)
    mock_execute.assert_called_once_with(query)
    assert result == []


def test_execute_query_unsafe_command_in_safe_mode(db_impl):
    """Test executing an unsafe command in safe mode."""
    query = "DROP TABLE nodes"
    with pytest.raises(ValueError):
        db_impl.execute_query(query)


def test_clear_database(mocker, db_impl):
    """Test clearing the database."""
    mock_execute = mocker.patch("duckdb.DuckDBPyConnection.execute")
    db_impl.clear_database()
    calls = [call("DROP TABLE IF EXISTS edges"), call("DROP TABLE IF EXISTS nodes")]
    mock_execute.assert_has_calls(calls, any_order=True)


def test_get_human_response(mocker, db_impl):
    """Test getting a human response from the database."""
    mock_invoke = mocker.patch("langchain.chains.base.Chain.invoke", return_value={"output": "response"})
    mock_invoke.return_value = {"output": "response"}
    prompt = "What is the capital of France?"
    response = db_impl.get_human_response(prompt)
    mock_invoke.assert_called_once_with(prompt)
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
    mock_invoke.assert_called_once_with(prompt)
    assert response == "response"


def test_create_edges(mocker, db_impl):
    """Test creating edges in the database."""
    mock_executemany = mocker.patch("duckdb.DuckDBPyConnection.executemany")
    edges = [("subject1", "predicate1", "object1"), ("subject2", "predicate2", "object2")]
    db_impl.create_edges(edges)
    mock_executemany.assert_called_once_with(
        "INSERT INTO edges (subject, predicate, object) VALUES (?, ?, ?)",
        edges,
    )


def test_create_nodes(mocker, db_impl):
    """Test creating nodes in the database."""
    mock_executemany = mocker.patch("duckdb.DuckDBPyConnection.executemany")
    nodes = [("id1", "category1", "label1"), ("id2", "category2", "label2")]
    db_impl.create_nodes(nodes)
    mock_executemany.assert_called_once_with(
        "INSERT INTO nodes (id, category, label) VALUES (?, ?, ?)",
        nodes,
    )


def test_show_schema(mocker, db_impl):
    """Test showing the schema of the database."""
    mock_execute = mocker.patch("duckdb.DuckDBPyConnection.execute")
    mock_execute.return_value.fetchall.return_value = [("nodes",), ("edges",)]
    result = db_impl.show_schema()
    mock_execute.assert_called_once_with("PRAGMA show_tables")
    assert result is None  # pprint returns None


def test_execute_query_using_langchain(mocker, db_impl):
    """Test executing a query using the langchain agent."""
    mock_invoke = mocker.patch("langchain.chains.base.Chain.invoke", return_value={"output": "response"})
    mock_invoke.return_value = {"output": "response"}
    prompt = "Get all nodes"
    response = db_impl.execute_query_using_langchain(prompt)
    mock_invoke.assert_called_once_with(prompt)
    assert response == "response"
