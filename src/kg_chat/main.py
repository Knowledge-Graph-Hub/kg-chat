"""Main module for the KG Chat application."""

from os import getenv
from pprint import pprint

from langchain.chains import GraphCypherQAChain
from langchain.memory import ConversationBufferMemory
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from neo4j import GraphDatabase

from kg_chat.utils import import_kg_into_neo4j

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
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
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
            username="neo4j",  # Replace with your Neo4j username
            password="password",  # Replace with your Neo4j password
        )

        # Initialize LLM
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

        # Initialize chain with memory
        chain = GraphCypherQAChain.from_llm(graph=graph, llm=llm, verbose=True, memory=memory)

        while True:
            query = input("Ask me about your data! : ")
            if query.lower() in ["exit", "quit"]:
                print("Exiting the interactive session.")
                break

            # Invoke the chain with the query
            response = chain.invoke({"query": query})

            # Store the query and response in memory
            memory.chat_memory.add_user_message(query)
            memory.chat_memory.add_ai_message(response["result"])

            # Print the result
            pprint(response["result"])

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    load_neo4j()
