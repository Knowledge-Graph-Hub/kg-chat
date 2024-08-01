"""Main module for the KG Chat application."""

import json
from pprint import pprint

from langchain.memory import ConversationBufferMemory

from kg_chat.interface.database_interface import DatabaseInterface
from kg_chat.utils import extract_nodes_edges, visualize_kg


class KnowledgeGraphChat:
    """Main class for the KG Chatbot application."""

    def __init__(self, db: DatabaseInterface):
        """Initialize the KG Chatbot with a database interface."""
        self.db = db
        self.memory = ConversationBufferMemory()

    def load_database(self):
        """Load the Knowledge Graph into the database."""
        self.db.load_kg()

    def execute_query(self, query: str):
        """Execute a Cypher query against the Neo4j database."""
        # result = db.execute_query(query) #! Also an option to run directly through database
        return self.db.execute_query_using_langchain(query)

    def get_human_response(self, query: str):
        """Ask a question to the KG Chatbot and get a response."""
        return self.db.get_human_response(query)

    def get_structured_response(self, query: str):
        """Ask a question to the KG Chatbot and get a structured response."""
        return self.db.get_structured_response(query)

    def chat(self):
        """Start an interactive chat session with the KG Chatbot."""
        try:
            while True:
                prompt = input("Ask me about your data! : ")
                if prompt.lower() in ["exit", "quit"]:
                    print("Exiting the interactive session.")
                    break

                response = self.get_structured_response(prompt)
                result = response["output"] if "output" in response else response

                # Store the query and response in memory
                self.memory.chat_memory.add_user_message(prompt)
                self.memory.chat_memory.add_ai_message(result)

                # Print the result
                pprint(result)

                if "show me" in prompt.lower():
                    # Parse the string response into a dictionary
                    cleaned_result = result.replace("```", "").replace("json\n", "").replace("\n", "")

                    # Parse the cleaned string response into a dictionary
                    structured_result = json.loads(cleaned_result)

                    # Visualize the KG

                    nodes, edges = extract_nodes_edges(structured_result)
                    visualize_kg(nodes, edges)

        except Exception as e:
            print(f"An error occurred: {e}")
