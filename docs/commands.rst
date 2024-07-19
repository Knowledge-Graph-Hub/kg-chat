Commands
========

1. ``import``: This loads the nodes and edges file into a Neo4j instance. This will take a while depending on the size of the tsv files.

    .. code-block:: shell

        poetry run kg import

2. ``test-query``: To test that the above worked, run a built-in test query:

    .. code-block:: shell

        poetry run kg test-query --database neo4j

    This should return something like (as per KGX data in the repo):

    .. code-block:: shell

        {'n': {'label': 'Streptomyces thermocarboxydovorans', 'id': 'NCBITaxon:59298'}}
        {'n': {'label': 'Streptomyces thermocarboxydus', 'id': 'NCBITaxon:59299'}}
        {'n': {'label': 'Streptomyces thermogriseus', 'id': 'NCBITaxon:75292'}}
        {'n': {'label': 'Streptomyces thermospinosisporus', 'id': 'NCBITaxon:161482'}}
        {'n': {'label': 'Streptomyces vitaminophilus', 'id': 'NCBITaxon:76728'}}
        {'n': {'label': 'Streptomyces yanii', 'id': 'NCBITaxon:78510'}}
        {'n': {'label': 'Kitasatospora azatica', 'id': 'NCBITaxon:58347'}}
        {'n': {'label': 'Kitasatospora paracochleata', 'id': 'NCBITaxon:58354'}}
        {'n': {'label': 'Kitasatospora putterlickiae', 'id': 'NCBITaxon:221725'}}
        {'n': {'label': 'Kitasatospora sampliensis', 'id': 'NCBITaxon:228655'}}

3. ``qna``: This command can be used for asking a question about the data and receiving a response.

    .. code-block:: shell

        poetry run kg qna --database neo4j "give me the sorted (descending) frequency count nodes with relationships. Give me label and id. I want this as a table "

    This should return

    .. code-block:: text

        > Entering new GraphCypherQAChain chain...
        Generated Cypher:
        MATCH (n:Node)-[r:RELATIONSHIP]->(m:Node)
        RETURN n.label AS label, n.id AS id, COUNT(r) AS frequency
        ORDER BY frequency DESC
        Full Context:
        [{'label': 'hydrocarbon', 'id': 'CHEBI:24632', 'frequency': 2381}, {'label': 'Marinobacterium coralli', 'id': 'NCBITaxon:693965', 'frequency': 55}, {'label': 'Marinobacterium coralli LMG 25435', 'id': 'NCBITaxon:693965', 'frequency': 55}, {'label': 'Ruegeria mobilis DSM 23403', 'id': 'NCBITaxon:379347', 'frequency': 47}, {'label': 'Ruegeria mobilis S1942', 'id': 'NCBITaxon:379347', 'frequency': 47}, {'label': 'Ruegeria pelagia', 'id': 'NCBITaxon:379347', 'frequency': 47}, {'label': 'ruegeria_pelagia', 'id': 'NCBITaxon:379347', 'frequency': 47}, {'label': 'ruegeria_mobilis', 'id': 'NCBITaxon:379347', 'frequency': 47}, {'label': 'Ruegeria mobilis', 'id': 'NCBITaxon:379347', 'frequency': 47}, {'label': 'Ruegeria mobilis 45A6', 'id': 'NCBITaxon:379347', 'frequency': 47}]

        > Finished chain.
        ('| Label                        | ID              | Frequency |\n'
        '|------------------------------|-----------------|-----------|\n'
        '| hydrocarbon                  | CHEBI:24632     | 2381      |\n'
        '| Marinobacterium coralli      | NCBITaxon:693965| 55        |\n'
        '| Ruegeria mobilis             | NCBITaxon:379347| 47        |\n'
        '| Ruegeria pelagia             | NCBITaxon:379347| 47        |\n'
        '| Ruegeria mobilis DSM 23403   | NCBITaxon:379347| 47        |\n'
        '| Ruegeria mobilis S1942       | NCBITaxon:379347| 47        |\n'
        '| Ruegeria pelagia             | NCBITaxon:379347| 47        |\n'
        '| ruegeria_pelagia             | NCBITaxon:379347| 47        |\n'
        '| ruegeria_mobilis             | NCBITaxon:379347| 47        |\n'
        '| Ruegeria mobilis 45A6        | NCBITaxon:379347| 47        |')

4. ``chat``: This starts an interactive chat session where you can ask questions about your KG.

    .. code-block:: shell

        poetry run kg chat --database neo4j

    Gives you the following:

    .. code-block:: shell

        Ask me about your data! : 

    To quit type ``quit`` or ``exit``.

    Example conversation:
    """"""""""""""""""""""
    
    .. code-block:: shell

        Ask me about your data! : Give me a brief statistic about the table

        > Entering new GraphCypherQAChain chain...
        Generated Cypher:
        MATCH (n:Node)-[r:RELATIONSHIP]->(m:Node)
        RETURN COUNT(n) AS nodeCount, COUNT(r) AS relationshipCount
        Full Context:
        [{'nodeCount': 598598, 'relationshipCount': 598598}]

        > Finished chain.
        'The table contains 598,598 nodes and 598,598 relationships.'
        Ask me about your data! : give me a table of the 5 most frequent relationships

        > Entering new GraphCypherQAChain chain...
        Generated Cypher:
        cypher
        MATCH ()-[r:RELATIONSHIP]->()
        RETURN r.type AS RelationshipType, COUNT(r) AS Frequency
        ORDER BY Frequency DESC
        LIMIT 5

        Full Context:
        [{'RelationshipType': 'biolink:capable_of', 'Frequency': 225052}, {'RelationshipType': 'biolink:location_of', 'Frequency': 187104}, {'RelationshipType': 'biolink:consumes', 'Frequency': 107037}, {'RelationshipType': 'biolink:has_phenotype', 'Frequency': 79168}, {'RelationshipType': 'biolink:has_chemical_role', 'Frequency': 237}]

        > Finished chain.
        ('| Relationship Type            | Frequency |\n'
        '|------------------------------|-----------|\n'
        '| biolink:capable_of           | 225052    |\n'
        '| biolink:location_of          | 187104    |\n'
        '| biolink:consumes             | 107037    |\n'
        '| biolink:has_phenotype        | 79168     |\n'
        '| biolink:has_chemical_role    | 237       |')
        Ask me about your data! : Give me node IDs and labels of any 10 nodes that have the word strep in it

        > Entering new GraphCypherQAChain chain...
        Generated Cypher:
        cypher
        MATCH (n:Node)
        WHERE n.label CONTAINS 'strep'
        RETURN n.id, n.label
        LIMIT 10

        Full Context:
        [{'n.id': 'NCBITaxon:33035', 'n.label': 'Peptostreptococcus productus'}, {'n.id': 'NCBITaxon:596329', 'n.label': 'Peptostreptococcus anaerobius 653-L'}, {'n.id': 'NCBITaxon:1261', 'n.label': 'Peptostreptococcus anaerobius'}, {'n.id': 'NCBITaxon:596315', 'n.label': 'Peptostreptococcus stomatis DSM 17678'}, {'n.id': 'NCBITaxon:1262', 'n.label': 'Peptostreptococcus sp. 2'}, {'n.id': 'NCBITaxon:1261', 'n.label': 'Peptostreptococcus anaerobius 0009-10 Hillier'}, {'n.id': 'NCBITaxon:1262', 'n.label': 'Peptostreptococcus sp. ACS-065-V-Col13'}, {'n.id': 'NCBITaxon:796937', 'n.label': 'Peptostreptococcaceae bacterium CM2'}, {'n.id': 'NCBITaxon:796937', 'n.label': 'Peptostreptococcaceae bacterium ACC19a'}, {'n.id': 'NCBITaxon:796937', 'n.label': 'Peptostreptococcaceae bacterium CM5'}]

        > Finished chain.
        ('Here are the node IDs and labels of 10 nodes that have the word "strep" in '
        'them:\n'
        '\n'
        '1. NCBITaxon:33035 - Peptostreptococcus productus\n'
        '2. NCBITaxon:596329 - Peptostreptococcus anaerobius 653-L\n'
        '3. NCBITaxon:1261 - Peptostreptococcus anaerobius\n'
        '4. NCBITaxon:596315 - Peptostreptococcus stomatis DSM 17678\n'
        '5. NCBITaxon:1262 - Peptostreptococcus sp. 2\n'
        '6. NCBITaxon:1261 - Peptostreptococcus anaerobius 0009-10 Hillier\n'
        '7. NCBITaxon:1262 - Peptostreptococcus sp. ACS-065-V-Col13\n'
        '8. NCBITaxon:796937 - Peptostreptococcaceae bacterium CM2\n'
        '9. NCBITaxon:796937 - Peptostreptococcaceae bacterium ACC19a\n'
        '10. NCBITaxon:796937 - Peptostreptococcaceae bacterium CM5')

    Visualization
    """""""""""""

    If the prompt has the phrase ``show me`` in it, ``kg-chat`` would render an HTML output with KG representation of the response. 
    
    This example was run over local data that is not not in version control due to size restrictions:

    .. code-block:: shell

        kg-chat $ poetry run kg chat
        Ask me about your data! : show me 20 edges with subject prefix = Uniprot  


        > Entering new SQL Agent Executor chain...

        Invoking: `sql_db_list_tables` with `{}`


        edges, nodes
        Invoking: `sql_db_schema` with `{'table_names': 'edges, nodes'}`



        CREATE TABLE edges (
                subject VARCHAR, 
                predicate VARCHAR, 
                object VARCHAR
        )

        /*
        3 rows from edges table:
        subject predicate       object
        CHEBI:111503    biolink:binds   UniprotKB:H2K885
        CHEBI:111503    biolink:binds   UniprotKB:Q15JG1
        CHEBI:11851     biolink:binds   UniprotKB:A0A7C4JVU2
        */


        CREATE TABLE nodes (
                id VARCHAR NOT NULL, 
                category VARCHAR, 
                label VARCHAR
        )

        /*
        3 rows from nodes table:
        id      category        label
        UniprotKB:A0A5B8I2N0    biolink:Enzyme  Kynureninase 
        Proteomes:UP000320717   biolink:Genome  Proteomes:UP000320717
        UniprotKB:A0A5B8I3L9    biolink:Enzyme  Bifunctional protein GlmU (Includes: UDP-N-acetylglucosamine pyrophosphorylase 
        */
        Invoking: `sql_db_query_checker` with `{'query': "SELECT * FROM edges WHERE subject LIKE 'Uniprot%' LIMIT 20"}`


        ```sql
        SELECT * FROM edges WHERE subject LIKE 'Uniprot%' LIMIT 20
        ```
        Invoking: `sql_db_query` with `{'query': "SELECT * FROM edges WHERE subject LIKE 'Uniprot%' LIMIT 20"}`


        [('UniprotKB:A0A009GYQ4', 'biolink:located_in', 'GO:0009279'), ('UniprotKB:A0A009GYQ4', 'biolink:derives_from', 'Proteomes:UP000020595'), ('UniprotKB:A0A009GYV0', 'biolink:derives_from', 'Proteomes:UP000020595'), ('UniprotKB:A0A009GYV0', 'biolink:participates_in', 'GO:0009381'), ('UniprotKB:A0A009GZA8', 'biolink:participates_in', 'GO:0016491'), ('UniprotKB:A0A009GZA8', 'biolink:participates_in', 'GO:0006081'), ('UniprotKB:A0A009GZA8', 'biolink:derives_from', 'Proteomes:UP000020595'), ('UniprotKB:A0A009H0Q1', 'biolink:participates_in', 'GO:0047569'), ('UniprotKB:A0A009H0Q1', 'biolink:derives_from', 'Proteomes:UP000020595'), ('UniprotKB:A0A009H0Z9', 'biolink:derives_from', 'Proteomes:UP000020595'), ('UniprotKB:A0A009H2B9', 'biolink:derives_from', 'Proteomes:UP000020595'), ('UniprotKB:A0A009H2B9', 'biolink:located_in', 'GO:0016020'), ('UniprotKB:A0A009H2F4', 'biolink:derives_from', 'Proteomes:UP000020595'), ('UniprotKB:A0A009H2F4', 'biolink:participates_in', 'GO:0008168'), ('UniprotKB:A0A009H2F4', 'biolink:participates_in', 'GO:0032259'), ('UniprotKB:A0A009H2F4', 'biolink:participates_in', 'GO:0006744'), ('UniprotKB:A0A009H2L0', 'biolink:derives_from', 'Proteomes:UP000020595'), ('UniprotKB:A0A009H2N6', 'biolink:derives_from', 'Proteomes:UP000020595'), ('UniprotKB:A0A009H2W7', 'biolink:derives_from', 'Proteomes:UP000020595'), ('UniprotKB:A0A009H3M0', 'biolink:derives_from', 'Proteomes:UP000020595')]```json
        {
            "nodes": [
                {"label": "Kynureninase", "id": "UniprotKB:A0A5B8I2N0", "category": "biolink:Enzyme"},
                {"label": "Proteomes:UP000320717", "id": "Proteomes:UP000320717", "category": "biolink:Genome"},
                {"label": "Bifunctional protein GlmU (Includes: UDP-N-acetylglucosamine pyrophosphorylase", "id": "UniprotKB:A0A5B8I3L9", "category": "biolink:Enzyme"}
            ],
            "edges": [
                {"subject": {"label": "UniprotKB:A0A009GYQ4", "id": "UniprotKB:A0A009GYQ4"}, "object": {"label": "GO:0009279", "id": "GO:0009279"}, "predicate": "biolink:located_in"},
                {"subject": {"label": "UniprotKB:A0A009GYQ4", "id": "UniprotKB:A0A009GYQ4"}, "object": {"label": "Proteomes:UP000020595", "id": "Proteomes:UP000020595"}, "predicate": "biolink:derives_from"},
                {"subject": {"label": "UniprotKB:A0A009GYV0", "id": "UniprotKB:A0A009GYV0"}, "object": {"label": "Proteomes:UP000020595", "id": "Proteomes:UP000020595"}, "predicate": "biolink:derives_from"},
                {"subject": {"label": "UniprotKB:A0A009GYV0", "id": "UniprotKB:A0A009GYV0"}, "object": {"label": "GO:0009381", "id": "GO:0009381"}, "predicate": "biolink:participates_in"},
                {"subject": {"label": "UniprotKB:A0A009GZA8", "id": "UniprotKB:A0A009GZA8"}, "object": {"label": "GO:0016491", "id": "GO:0016491"}, "predicate": "biolink:participates_in"},
                {"subject": {"label": "UniprotKB:A0A009GZA8", "id": "UniprotKB:A0A009GZA8"}, "object": {"label": "GO:0006081", "id": "GO:0006081"}, "predicate": "biolink:participates_in"},
                {"subject": {"label": "UniprotKB:A0A009GZA8", "id": "UniprotKB:A0A009GZA8"}, "object": {"label": "Proteomes:UP000020595", "id": "Proteomes:UP000020595"}, "predicate": "biolink:derives_from"},
                {"subject": {"label": "UniprotKB:A0A009H0Q1", "id": "UniprotKB:A0A009H0Q1"}, "object": {"label": "GO:0047569", "id": "GO:0047569"}, "predicate": "biolink:participates_in"},
                {"subject": {"label": "UniprotKB:A0A009H0Q1", "id": "UniprotKB:A0A009H0Q1"}, "object": {"label": "Proteomes:UP000020595", "id": "Proteomes:UP000020595"}, "predicate": "biolink:derives_from"},
                {"subject": {"label": "UniprotKB:A0A009H0Z9", "id": "UniprotKB:A0A009H0Z9"}, "object": {"label": "Proteomes:UP000020595", "id": "Proteomes:UP000020595"}, "predicate": "biolink:derives_from"},
                {"subject": {"label": "UniprotKB:A0A009H2B9", "id": "UniprotKB:A0A009H2B9"}, "object": {"label": "Proteomes:UP000020595", "id": "Proteomes:UP000020595"}, "predicate": "biolink:derives_from"},
                {"subject": {"label": "UniprotKB:A0A009H2B9", "id": "UniprotKB:A0A009H2B9"}, "object": {"label": "GO:0016020", "id": "GO:0016020"}, "predicate": "biolink:located_in"},
                {"subject": {"label": "UniprotKB:A0A009H2F4", "id": "UniprotKB:A0A009H2F4"}, "object": {"label": "Proteomes:UP000020595", "id": "Proteomes:UP000020595"}, "predicate": "biolink:derives_from"},
                {"subject": {"label": "UniprotKB:A0A009H2F4", "id": "UniprotKB:A0A009H2F4"}, "object": {"label": "GO:0008168", "id": "GO:0008168"}, "predicate": "biolink:participates_in"},
                {"subject": {"label": "UniprotKB:A0A009H2F4", "id": "UniprotKB:A0A009H2F4"}, "object": {"label": "GO:0032259", "id": "GO:0032259"}, "predicate": "biolink:participates_in"},
                {"subject": {"label": "UniprotKB:A0A009H2F4", "id": "UniprotKB:A0A009H2F4"}, "object": {"label": "GO:0006744", "id": "GO:0006744"}, "predicate": "biolink:participates_in"},
                {"subject": {"label": "UniprotKB:A0A009H2L0", "id": "UniprotKB:A0A009H2L0"}, "object": {"label": "Proteomes:UP000020595", "id": "Proteomes:UP000020595"}, "predicate": "biolink:derives_from"},
                {"subject": {"label": "UniprotKB:A0A009H2N6", "id": "UniprotKB:A0A009H2N6"}, "object": {"label": "Proteomes:UP000020595", "id": "Proteomes:UP000020595"}, "predicate": "biolink:derives_from"},
                {"subject": {"label": "UniprotKB:A0A009H2W7", "id": "UniprotKB:A0A009H2W7"}, "object": {"label": "Proteomes:UP000020595", "id": "Proteomes:UP000020595"}, "predicate": "biolink:derives_from"},
                {"subject": {"label": "UniprotKB:A0A009H3M0", "id": "UniprotKB:A0A009H3M0"}, "object": {"label": "Proteomes:UP000020595", "id": "Proteomes:UP000020595"}, "predicate": "biolink:derives_from"}
            ]
        }
        ```

        > Finished chain.
        ('```json\n'
        '{\n'
        '    "nodes": [\n'
        '        {"label": "Kynureninase", "id": "UniprotKB:A0A5B8I2N0", "category": '
        '"biolink:Enzyme"},\n'
        '        {"label": "Proteomes:UP000320717", "id": "Proteomes:UP000320717", '
        '"category": "biolink:Genome"},\n'
        '        {"label": "Bifunctional protein GlmU (Includes: '
        'UDP-N-acetylglucosamine pyrophosphorylase", "id": "UniprotKB:A0A5B8I3L9", '
        '"category": "biolink:Enzyme"}\n'
        '    ],\n'
        '    "edges": [\n'
        '        {"subject": {"label": "UniprotKB:A0A009GYQ4", "id": '
        '"UniprotKB:A0A009GYQ4"}, "object": {"label": "GO:0009279", "id": '
        '"GO:0009279"}, "predicate": "biolink:located_in"},\n'
        '        {"subject": {"label": "UniprotKB:A0A009GYQ4", "id": '
        '"UniprotKB:A0A009GYQ4"}, "object": {"label": "Proteomes:UP000020595", "id": '
        '"Proteomes:UP000020595"}, "predicate": "biolink:derives_from"},\n'
        '        {"subject": {"label": "UniprotKB:A0A009GYV0", "id": '
        '"UniprotKB:A0A009GYV0"}, "object": {"label": "Proteomes:UP000020595", "id": '
        '"Proteomes:UP000020595"}, "predicate": "biolink:derives_from"},\n'
        '        {"subject": {"label": "UniprotKB:A0A009GYV0", "id": '
        '"UniprotKB:A0A009GYV0"}, "object": {"label": "GO:0009381", "id": '
        '"GO:0009381"}, "predicate": "biolink:participates_in"},\n'
        '        {"subject": {"label": "UniprotKB:A0A009GZA8", "id": '
        '"UniprotKB:A0A009GZA8"}, "object": {"label": "GO:0016491", "id": '
        '"GO:0016491"}, "predicate": "biolink:participates_in"},\n'
        '        {"subject": {"label": "UniprotKB:A0A009GZA8", "id": '
        '"UniprotKB:A0A009GZA8"}, "object": {"label": "GO:0006081", "id": '
        '"GO:0006081"}, "predicate": "biolink:participates_in"},\n'
        '        {"subject": {"label": "UniprotKB:A0A009GZA8", "id": '
        '"UniprotKB:A0A009GZA8"}, "object": {"label": "Proteomes:UP000020595", "id": '
        '"Proteomes:UP000020595"}, "predicate": "biolink:derives_from"},\n'
        '        {"subject": {"label": "UniprotKB:A0A009H0Q1", "id": '
        '"UniprotKB:A0A009H0Q1"}, "object": {"label": "GO:0047569", "id": '
        '"GO:0047569"}, "predicate": "biolink:participates_in"},\n'
        '        {"subject": {"label": "UniprotKB:A0A009H0Q1", "id": '
        '"UniprotKB:A0A009H0Q1"}, "object": {"label": "Proteomes:UP000020595", "id": '
        '"Proteomes:UP000020595"}, "predicate": "biolink:derives_from"},\n'
        '        {"subject": {"label": "UniprotKB:A0A009H0Z9", "id": '
        '"UniprotKB:A0A009H0Z9"}, "object": {"label": "Proteomes:UP000020595", "id": '
        '"Proteomes:UP000020595"}, "predicate": "biolink:derives_from"},\n'
        '        {"subject": {"label": "UniprotKB:A0A009H2B9", "id": '
        '"UniprotKB:A0A009H2B9"}, "object": {"label": "Proteomes:UP000020595", "id": '
        '"Proteomes:UP000020595"}, "predicate": "biolink:derives_from"},\n'
        '        {"subject": {"label": "UniprotKB:A0A009H2B9", "id": '
        '"UniprotKB:A0A009H2B9"}, "object": {"label": "GO:0016020", "id": '
        '"GO:0016020"}, "predicate": "biolink:located_in"},\n'
        '        {"subject": {"label": "UniprotKB:A0A009H2F4", "id": '
        '"UniprotKB:A0A009H2F4"}, "object": {"label": "Proteomes:UP000020595", "id": '
        '"Proteomes:UP000020595"}, "predicate": "biolink:derives_from"},\n'
        '        {"subject": {"label": "UniprotKB:A0A009H2F4", "id": '
        '"UniprotKB:A0A009H2F4"}, "object": {"label": "GO:0008168", "id": '
        '"GO:0008168"}, "predicate": "biolink:participates_in"},\n'
        '        {"subject": {"label": "UniprotKB:A0A009H2F4", "id": '
        '"UniprotKB:A0A009H2F4"}, "object": {"label": "GO:0032259", "id": '
        '"GO:0032259"}, "predicate": "biolink:participates_in"},\n'
        '        {"subject": {"label": "UniprotKB:A0A009H2F4", "id": '
        '"UniprotKB:A0A009H2F4"}, "object": {"label": "GO:0006744", "id": '
        '"GO:0006744"}, "predicate": "biolink:participates_in"},\n'
        '        {"subject": {"label": "UniprotKB:A0A009H2L0", "id": '
        '"UniprotKB:A0A009H2L0"}, "object": {"label": "Proteomes:UP000020595", "id": '
        '"Proteomes:UP000020595"}, "predicate": "biolink:derives_from"},\n'
        '        {"subject": {"label": "UniprotKB:A0A009H2N6", "id": '
        '"UniprotKB:A0A009H2N6"}, "object": {"label": "Proteomes:UP000020595", "id": '
        '"Proteomes:UP000020595"}, "predicate": "biolink:derives_from"},\n'
        '        {"subject": {"label": "UniprotKB:A0A009H2W7", "id": '
        '"UniprotKB:A0A009H2W7"}, "object": {"label": "Proteomes:UP000020595", "id": '
        '"Proteomes:UP000020595"}, "predicate": "biolink:derives_from"},\n'
        '        {"subject": {"label": "UniprotKB:A0A009H3M0", "id": '
        '"UniprotKB:A0A009H3M0"}, "object": {"label": "Proteomes:UP000020595", "id": '
        '"Proteomes:UP000020595"}, "predicate": "biolink:derives_from"}\n'
        '    ]\n'
        '}\n'
        '```')
        ../kg-chat/src/kg_chat/graph_output/knowledge_graph.html
        Ask me about your data! : 


    This results in the formation of the knowledge_graph.html file.
    
    .. image:: ../src/kg_chat/assets/kg_viz.png
        :alt: alternate text
        :align: center


5. ``app``: This command can be used to start the KG chat app.

    .. code-block:: shell

        poetry run kg app

    This will start the app on http://localhost:8050/ which can be accessed in the browser.

    Example:

    .. image:: ../src/kg_chat/assets/kg_app.png
       :alt: chat interface
       :align: center
    