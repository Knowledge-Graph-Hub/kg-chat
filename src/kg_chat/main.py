from os import getenv
from pprint import pprint
from neo4j import GraphDatabase
from langchain.chains import GraphCypherQAChain
from langchain_openai import ChatOpenAI

from kg_chat.utils import import_kg_into_neo4j
from langchain_community.graphs import Neo4jGraph

# Set environment variables for Neo4j connection
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password"

OPENAI_KEY = getenv("OPENAI_API_KEY")

def load_neo4j():
    """Define API."""
    import_kg_into_neo4j()

def execute_query_using_neo4j(query):
    """Execute a Cypher query against the Neo4j database."""
    # Initialize the Neo4j driver
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    def run_query(tx):
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

def question_and_answer(query:str):
    graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    chain = GraphCypherQAChain.from_llm(graph=graph, llm=llm, verbose=True)
    response = chain.invoke({"query": query})
    pprint(response['result'])


if __name__ == "__main__":
    load_neo4j()

