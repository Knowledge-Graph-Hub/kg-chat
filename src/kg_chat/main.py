"""Main module for the KG Chat application."""

import json
from os import getenv
from pprint import pprint

from langchain.chains import GraphCypherQAChain
from langchain.memory import ConversationBufferMemory
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from neo4j import GraphDatabase

from kg_chat.constants import MODEL, NEO4J_PASSWORD, NEO4J_USERNAME
from kg_chat.utils import extract_nodes_edges, import_kg_into_neo4j, visualize_kg

# Set environment variables for Neo4j connection
NEO4J_URI = "bolt://localhost:7687"

OPENAI_KEY = getenv("OPENAI_API_KEY")


def load_neo4j():
    """Define API."""
    import_kg_into_neo4j()


def execute_query_using_neo4j(query):
    """Execute a Cypher query against the Neo4j database."""
    # Initialize the Neo4j driver
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

    def run_query(tx):
        """Run the query within a transaction."""
        return list(tx.run(query))

    # Execute the query within a session
    with driver.session() as session:
        result = session.read_transaction(run_query)

    # Close the driver connection
    driver.close()

    return result


def execute_query_using_langchain(query):
    """Execute a Cypher query against the Neo4j database."""
    # Initialize the Neo4jGraph object
    neo4j_graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)

    # Execute the query
    result = neo4j_graph.query(query)

    return result


def question_and_answer(query: str):
    """Ask a question to the KG Chatbot and get a response."""
    graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
    llm = ChatOpenAI(model=MODEL, temperature=0)
    chain = GraphCypherQAChain.from_llm(graph=graph, llm=llm, verbose=True)
    response = chain.invoke({"query": query})
    pprint(response["result"])


def chat():
    """Start an interactive chat session with the KG Chatbot."""
    memory = ConversationBufferMemory()
    try:
        # Initialize Neo4j graph connection using LangChain's Neo4jGraph
        graph = Neo4jGraph(
            url="bolt://localhost:7687",  # Replace with your Neo4j URI
            username=NEO4J_USERNAME,  # Replace with your Neo4j username
            password=NEO4J_PASSWORD,  # Replace with your Neo4j password
        )

        # Initialize LLM
        llm = ChatOpenAI(model=MODEL, temperature=0)

        # Initialize chain with memory
        chain = GraphCypherQAChain.from_llm(graph=graph, llm=llm, verbose=True, memory=memory)

        while True:
            query = input("Ask me about your data! : ")
            if query.lower() in ["exit", "quit"]:
                print("Exiting the interactive session.")
                break

            if "show me" in query.lower():
                # Modify the query to request structured results
                structured_query = f"""
                {query}
                Please provide the result in JSON format with nodes and edges.
                Example: {{
                    "nodes": [
                        {{"label": "A", "id": "1"}},
                        {{"label": "B", "id": "2"}},
                        {{"label": "C", "id": "3"}}
                    ],
                    "edges": [
                        {{"source": {{"label": "A", "id": "1"}},
                        "target": {{"label": "B", "id": "2"}},
                        "relationship": "biolink:related_to"}}
                    ]
                }}
                """

            else:
                structured_query = query

            # Invoke the chain with the modified query
            response = chain.invoke({"query": structured_query})

            # Store the query and response in memory
            memory.chat_memory.add_user_message(query)
            memory.chat_memory.add_ai_message(response["result"])

            # Print the result
            pprint(response["result"])

            if "show me" in query.lower():
                # Parse the string response into a dictionary
                cleaned_result = response["result"].replace("```", "").replace("json\n", "").replace("\n", "")

                # Parse the cleaned string response into a dictionary
                structured_result = json.loads(cleaned_result)

                # Visualize the KG

                nodes, edges = extract_nodes_edges(structured_result)
                visualize_kg(nodes, edges)

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    load_neo4j()
