Examples
========

Here are some example prompts and their corresponding responses:

.. code-block:: shell

    kg-chat $ kg chat --database neo4j
    Ask me about your data! : How many nodes are there in the database?

    > Entering new GraphCypherQAChain chain...
    Generated Cypher:
    MATCH (n)
    RETURN COUNT(n) AS nodeCount

    Full Context:
    [{'nodeCount': 598598}]

    > Finished chain.
    'The database contains 598,598 nodes.'

.. code-block:: shell

    kg-chat $ kg chat --database neo4j
    Ask me about your data! : Show me the first 5 nodes

    > Entering new GraphCypherQAChain chain...
    Generated Cypher:
    MATCH (n)
    RETURN n
    LIMIT 5

    Full Context:
    [{'n': {'id': 'NCBITaxon:1', 'label': 'root'}}, {'n': {'id': 'NCBITaxon:2', 'label': 'Bacteria'}}, {'n': {'id': 'NCBITaxon:6', 'label': 'Azorhizobium caulinodans'}}, {'n': {'id': 'NCBITaxon:7', 'label': 'Azotobacter vinelandii'}}, {'n': {'id': 'NCBITaxon:9', 'label': 'Bacillus subtilis'}}]

    > Finished chain.
    ('Here are the first 5 nodes:\n'
    '\n'
    '1. NCBITaxon:1 - root\n'
    '2. NCBITaxon:2 - Bacteria\n'
    '3. NCBITaxon:6 - Azorhizobium caulinodans\n'
    '4. NCBITaxon:7 - Azotobacter vinelandii\n'
    '5. NCBITaxon:9 - Bacillus subtilis')

.. code-block:: shell

    kg-chat $ kg chat --database neo4j
    Ask me about your data! : What is the most common relationship type?

    > Entering new GraphCypherQAChain chain...
    Generated Cypher:
    MATCH ()-[r]->()
    RETURN r.type AS RelationshipType, COUNT(r) AS Frequency
    ORDER BY Frequency DESC
    LIMIT 1

    Full Context:
    [{'RelationshipType': 'biolink:capable_of', 'Frequency': 225052}]

    > Finished chain.
    'The most common relationship type is "biolink:capable_of" with a frequency of 225,052.'
