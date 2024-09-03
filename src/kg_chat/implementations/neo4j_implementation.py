"""Implementation of the DatabaseInterface for Neo4j."""

import csv
import logging
import time
from pathlib import Path
from pprint import pprint
from typing import Any, Optional, Sequence, Union

from langchain.agents import Tool
from langchain.agents.agent import AgentExecutor
from langchain.agents.agent_types import AgentType
from langchain.agents.loading import AGENT_TO_CLASS, load_agent
from langchain.tools.retriever import create_retriever_tool
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain_core.callbacks import BaseCallbackManager
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool
from langchain_ollama import ChatOllama
from neo4j import GraphDatabase

from kg_chat.config.llm_config import LLMConfig
from kg_chat.constants import DATALOAD_BATCH_SIZE, NEO4J_PASSWORD, NEO4J_URI, NEO4J_USERNAME, VECTOR_DB_PATH
from kg_chat.interface.database_interface import DatabaseInterface
from kg_chat.utils import (
    create_vectorstore,
    get_cypher_agent_prompt_template,
    get_exisiting_vectorstore,
    llm_factory,
    structure_query,
)

logger = logging.getLogger(__name__)


class Neo4jImplementation(DatabaseInterface):
    """Implementation of the DatabaseInterface for Neo4j."""

    def __init__(
        self,
        data_dir: Union[str, Path],
        doc_dir_or_file: Union[str, Path] = None,
        uri: str = NEO4J_URI,
        username: str = NEO4J_USERNAME,
        password: str = NEO4J_PASSWORD,
        llm_config: LLMConfig = None,
    ):
        """Initialize the Neo4j database and the Langchain components."""
        if not data_dir:
            raise ValueError("Data directory is required. This typically contains the KGX tsv files.")
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.graph = Neo4jGraph(url=uri, username=username, password=password)
        self.llm = llm_factory(llm_config)
        self.tools = []
        self.data_dir = Path(data_dir)
        if VECTOR_DB_PATH.exists() and get_exisiting_vectorstore():
            vectorstore = get_exisiting_vectorstore()
            retriever = vectorstore.as_retriever(search_kwargs={"k": 1})
            rag_tool = create_retriever_tool(retriever, "VectorStoreRetriever", "Vector Store Retriever")

            self.tools.append(rag_tool)
        elif doc_dir_or_file:
            vectorstore = create_vectorstore(doc_dir_or_file=doc_dir_or_file)
            retriever = vectorstore.as_retriever(search_kwargs={"k": 1})
            rag_tool = create_retriever_tool(retriever, "VectorStoreRetriever", "Vector Store Retriever")
            self.tools.append(rag_tool)
        else:
            logger.info("No vectorstore found or documents provided. Skipping RAG tool creation.")

        graph_cypher_qa_chain = GraphCypherQAChain.from_llm(
            graph=self.graph,
            llm=self.llm,
            verbose=True,
            use_function_response=True,
            # function_response_system="Respond as a Data Scientist!",
            validate_cypher=True,
        )
        graph_cypher_qa_chain_tool = Tool(
            name="GraphCypherQAChain",
            description="Graph Cypher QA Chain",
            func=graph_cypher_qa_chain.invoke,
        )

        self.tools.append(graph_cypher_qa_chain_tool)
        self.tool_names = [tool.name for tool in self.tools]
        self.safe_mode = True
        self.agent_executor = self.initialize_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=get_cypher_agent_prompt_template(),
            handle_parsing_errors=True,
            verbose=True,
        )

        # self.agent_executor = AgentExecutor(
        #     agent=self.agent, tools=self.tools, handle_parsing_errors=True, verbose=True
        # )
        logger.info("Agent executor created successfully.")

    # ! Adoped from langchain.agents.initialize.initialize_agent since it'll be deprecated 1.0 onwards.
    # ! This works and `create_react_agent` which is the alternative doesn't work.
    @staticmethod
    def initialize_agent(
        tools: Sequence[BaseTool],
        llm: BaseLanguageModel,
        agent: Optional[AgentType] = None,
        callback_manager: Optional[BaseCallbackManager] = None,
        agent_path: Optional[str] = None,
        agent_kwargs: Optional[dict] = None,
        *,
        tags: Optional[Sequence[str]] = None,
        **kwargs: Any,
    ) -> AgentExecutor:
        """
        Load an agent executor given tools and LLM.

        :param tools: List of tools this agent has access to.
        :param llm: Language model to use as the agent.
        :param agent: Agent type to use. If None and agent_path is also None, will default
                    to AgentType.ZERO_SHOT_REACT_DESCRIPTION. Defaults to None.
        :param callback_manager: CallbackManager to use. Global callback manager is used if
                                not provided. Defaults to None.
        :param agent_path: Path to serialized agent to use. If None and agent is also None,
                        will default to AgentType.ZERO_SHOT_REACT_DESCRIPTION. Defaults to None.
        :param agent_kwargs: Additional keyword arguments to pass to the underlying agent.
                            Defaults to None.
        :param tags: Tags to apply to the traced runs. Defaults to None.
        :param kwargs: Additional keyword arguments passed to the agent executor.

        :returns: An agent executor.

        :raises ValueError: If both `agent` and `agent_path` are specified.
        :raises ValueError: If `agent` is not a valid agent type.
        :raises ValueError: If both `agent` and `agent_path` are None.
        """
        tags_ = list(tags) if tags else []
        if agent is None and agent_path is None:
            agent = AgentType.ZERO_SHOT_REACT_DESCRIPTION
        if agent is not None and agent_path is not None:
            raise ValueError("Both `agent` and `agent_path` are specified, " "but at most only one should be.")
        if agent is not None:
            if agent not in AGENT_TO_CLASS:
                raise ValueError(f"Got unknown agent type: {agent}. " f"Valid types are: {AGENT_TO_CLASS.keys()}.")
            tags_.append(agent.value if isinstance(agent, AgentType) else agent)
            agent_cls = AGENT_TO_CLASS[agent]
            agent_kwargs = agent_kwargs or {}
            agent_obj = agent_cls.from_llm_and_tools(llm, tools, callback_manager=callback_manager, **agent_kwargs)
        elif agent_path is not None:
            agent_obj = load_agent(agent_path, llm=llm, tools=tools, callback_manager=callback_manager)
            try:
                # TODO: Add tags from the serialized object directly.
                tags_.append(agent_obj._agent_type)
            except NotImplementedError:
                pass
        else:
            raise ValueError("Somehow both `agent` and `agent_path` are None, " "this should never happen.")

        return AgentExecutor.from_agent_and_tools(
            agent=agent_obj,
            tools=tools,
            callback_manager=callback_manager,
            tags=tags_,
            **kwargs,
        )

    def toggle_safe_mode(self, enabled: bool):
        """Toggle safe mode on or off."""
        self.safe_mode = enabled

    def is_safe_command(self, command: str) -> bool:
        """Check if a command is safe to execute."""
        unsafe_keywords = ["CREATE", "DELETE", "REMOVE", "SET", "MERGE", "DROP"]
        return not any(keyword in command.upper() for keyword in unsafe_keywords)

    def execute_unsafe_operation(self, operation: callable, *args, **kwargs):
        """Execute an unsafe operation."""
        original_safe_mode = self.safe_mode
        self.safe_mode = False
        try:
            result = operation(*args, **kwargs)
        finally:
            self.safe_mode = original_safe_mode
        return result

    def execute_query(self, query: str):
        """Execute a Cypher query against the Neo4j database."""
        if self.safe_mode and not self.is_safe_command(query):
            raise ValueError(f"Unsafe command detected: {query}")
        with self.driver.session() as session:
            result = session.read_transaction(lambda tx: list(tx.run(query)))
        return result

    def execute_query_using_langchain(self, query: str):
        """Execute a Cypher query against the Neo4j database using Langchain."""
        if self.safe_mode and not self.is_safe_command(query):
            raise ValueError(f"Unsafe command detected: {query}")
        result = self.graph.query(query)
        return result

    def clear_database(self):
        """Clear the Neo4j database."""

        def _clear_database():
            with self.driver.session() as session:
                session.write_transaction(self._clear_database_tx)

        return self.execute_unsafe_operation(_clear_database)

    @staticmethod
    def _clear_database_tx(tx):
        """Clear the Neo4j database using APOC."""
        tx.run(
            """
        CALL apoc.periodic.iterate(
            'MATCH (n) RETURN n',
            'DETACH DELETE n',
            {batchSize:1000, parallel:true}
        )
        """
        )

    def ensure_index(self):
        """Ensure that the index on :Node(id) exists."""

        def _ensure_index():
            with self.driver.session() as session:
                session.write_transaction(self._ensure_index_tx)

        return self.execute_unsafe_operation(_ensure_index)

    @staticmethod
    def _ensure_index_tx(tx):
        """Index existence check."""
        tx.run(
            """
            CALL apoc.schema.assert(
                {Node: [['id'], ['category'], ['label']]},
                {RELATIONSHIP: [['subject'], ['predicate'], ['object']]}
            )
            """
        )
        print("Indexes ensured using APOC.")

    def get_human_response(self, prompt: str):
        """Get a human response from the Neo4j database."""
        # human_response = self.chain.invoke({"query": prompt})
        human_response = self.agent_executor.invoke(
            {
                "input": prompt,
                "tools": self.tools,
                "tool_names": self.tool_names,
            }
        )

        pprint(human_response["output"])
        return human_response["output"]

    def get_structured_response(self, prompt: str):
        """Get a structured response from the Neo4j database."""
        if isinstance(self.llm, ChatOllama):
            if "show me" in prompt.lower():
                self.llm.format = "json"
        # response = self.chain.invoke({"query": structure_query(prompt)})
        response = self.agent_executor.invoke(
            {
                "input": structure_query(prompt),
                "tools": self.tools,
                "tool_names": self.tool_names,
            }
        )
        return response["output"]

    def create_edges(self, edges):
        """Create relationships between nodes."""

        def _create_edges():
            with self.driver.session() as session:
                session.write_transaction(self._create_edges_tx, edges)

        return self.execute_unsafe_operation(_create_edges)

    @staticmethod
    def _create_edges_tx(tx, edges):
        tx.run(
            """
            UNWIND $edges AS edge
            MATCH (a:Node {id: edge.subject})
            MATCH (b:Node {id: edge.object})
            CREATE (a)-[r:RELATIONSHIP {type: edge.predicate}]->(b)
        """,
            edges=edges,
        )

    def create_nodes(self, nodes):
        """Create nodes in the Neo4j database."""

        def _create_nodes():
            with self.driver.session() as session:
                session.write_transaction(self._create_nodes_tx, nodes)

        return self.execute_unsafe_operation(_create_nodes)

    @staticmethod
    def _create_nodes_tx(tx, nodes):
        tx.run(
            """
            UNWIND $nodes AS node
            CREATE (n:Node {id: node.id, category: node.category, label: node.label})
        """,
            nodes=nodes,
        )

    def show_schema(self):
        """Show the schema of the Neo4j database."""
        with self.driver.session() as session:
            result = session.read_transaction(lambda tx: list(tx.run("CALL db.schema.visualization()")))
            pprint(result)

    def load_kg(self, block_size: int = DATALOAD_BATCH_SIZE):
        """Load the Knowledge Graph into the Neo4j database."""
        nodes_filepath = self.data_dir / "nodes.tsv"
        edges_filepath = self.data_dir / "edges.tsv"

        def _load_kg():
            # Clear the existing database
            print("Clearing the existing database...")
            self.clear_database()
            print("Database cleared.")

            # Ensure indexes are created
            print("Ensuring indexes...")
            self.ensure_index()
            print("Indexes ensured.")

            # Import nodes in batches
            print("Starting to import nodes...")
            start_time = time.time()
            nodes_batch = []
            columns_of_interest = ["id", "category", "name", "description"]

            with open(nodes_filepath, "r") as nodes_file:
                reader = csv.DictReader(nodes_file, delimiter="\t")
                node_batch_loaded = 0

                # Determine which label column to use
                label_column = "name" if "name" in reader.fieldnames else "description"

                for row in reader:
                    node_id = row[columns_of_interest[0]]
                    node_category = row[columns_of_interest[1]]
                    node_label = row[label_column]
                    nodes_batch.append({"id": node_id, "category": node_category, "label": node_label})
                    node_batch_loaded += 1

                    if len(nodes_batch) >= block_size:
                        self.create_nodes(nodes_batch)
                        nodes_batch = []

                if nodes_batch:
                    self.create_nodes(nodes_batch)

            elapsed_time_seconds = time.time() - start_time

            if elapsed_time_seconds >= 3600:
                elapsed_time_hours = elapsed_time_seconds / 3600
                print(f"Nodes import completed: {node_batch_loaded} nodes in {elapsed_time_hours:.2f} hours.")
            else:
                elapsed_time_minutes = elapsed_time_seconds / 60
                print(f"Nodes import completed: {node_batch_loaded} nodes in {elapsed_time_minutes:.2f} minutes.")

            # Import edges in batches
            print("Starting to import edges...")
            start_time = time.time()
            edges_batch = []
            edge_column_of_interest = ["subject", "predicate", "object"]

            with open(edges_filepath, "r") as edges_file:
                reader = csv.DictReader(edges_file, delimiter="\t")
                edge_batch_loaded = 0

                for row in reader:
                    subject = row[edge_column_of_interest[0]]
                    predicate = row[edge_column_of_interest[1]]
                    object = row[edge_column_of_interest[2]]
                    edges_batch.append({"subject": subject, "predicate": predicate, "object": object})
                    edge_batch_loaded += 1

                    if len(edges_batch) >= block_size / 2:
                        self.create_edges(edges_batch)
                        edges_batch = []

                if edges_batch:
                    self.create_edges(edges_batch)

            elapsed_time_seconds = time.time() - start_time
            if elapsed_time_seconds >= 3600:
                elapsed_time_hours = elapsed_time_seconds / 3600
                print(f"Edges import completed: {edge_batch_loaded} edges in {elapsed_time_hours:.2f} hours.")
            else:
                elapsed_time_minutes = elapsed_time_seconds / 60
                print(f"Edges import completed: {edge_batch_loaded} edges in {elapsed_time_minutes:.2f} minutes.")

            print("Import process finished.")

        return self.execute_unsafe_operation(_load_kg)

    def __del__(self):
        """Ensure the driver is closed when the object is destroyed."""
        if hasattr(self, "driver"):
            self.driver.close()
