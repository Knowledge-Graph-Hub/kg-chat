Visualization
=============

If the prompt has the phrase ``show me`` in it, ``kg-chat`` would render an HTML output with KG representation of the response. For example:

.. code-block:: shell

    kg-chat $ kg chat --database neo4j
    Ask me about your data! : show me 1 node with prefix NCBITaxon: that has at least 3 edges but less than 10 edges

    > Entering new GraphCypherQAChain chain...
    Generated Cypher:
    cypher
    MATCH (n:Node)
    WHERE n.id STARTS WITH 'NCBITaxon:'
    WITH n, size((n)-[:RELATIONSHIP]->()) AS outDegree, size((n)<-[:RELATIONSHIP]-()) AS inDegree
    WHERE (outDegree + inDegree) >= 3 AND (outDegree + inDegree) < 10
    WITH n LIMIT 1
    MATCH (n)-[r:RELATIONSHIP]-(m:Node)
    RETURN {
        nodes: collect({label: n.label, id: n.id}) + collect({label: m.label, id: m.id}),
        edges: collect({source: {label: n.label, id: n.id}, target: {label: m.label, id: m.id}, relationship: r.type})
    } AS result

    Full Context:
    [{'result': {'nodes': [{'label': 'Hysterium', 'id': 'NCBITaxon:100026'}, {'label': 'Hysterium', 'id': 'NCBITaxon:100026'}, {'label': 'Hysterium', 'id': 'NCBITaxon:100026'}, {'label': 'Hysterium', 'id': 'NCBITaxon:100026'}, {'label': 'Hysterium', 'id': 'NCBITaxon:100026'}, {'label': 'Hysterium', 'id': 'NCBITaxon:100026'}, {'label': 'Hysterium', 'id': 'NCBITaxon:100026'}, {'label': 'Hysterium', 'id': 'NCBITaxon:100026'}, {'label': 'Hysterium vermiforme', 'id': 'NCBITaxon:714895'}, {'label': 'Hysterium barrianum', 'id': 'NCBITaxon:707625'}, {'label': 'Hysterium angustatum', 'id': 'NCBITaxon:574775'}, {'label': 'Hysterium hyalinum', 'id': 'NCBITaxon:574776'}, {'label': 'unclassified Hysterium', 'id': 'NCBITaxon:2649321'}, {'label': 'Hysterium rhizophorae', 'id': 'NCBITaxon:2066082'}, {'label': 'Hysterium pulicare', 'id': 'NCBITaxon:100027'}, {'label': 'Hysteriaceae', 'id': 'NCBITaxon:100025'}], 'edges': [{'source': {'label': 'Hysterium', 'id': 'NCBITaxon:100026'}, 'relationship': 'biolink:subclass_of', 'target': {'label': 'Hysterium vermiforme', 'id': 'NCBITaxon:714895'}}, {'source': {'label': 'Hysterium', 'id': 'NCBITaxon:100026'}, 'relationship': 'biolink:subclass_of', 'target': {'label': 'Hysterium barrianum', 'id': 'NCBITaxon:707625'}}, {'source': {'label': 'Hysterium', 'id': 'NCBITaxon:100026'}, 'relationship': 'biolink:subclass_of', 'target': {'label': 'Hysterium angustatum', 'id': 'NCBITaxon:574775'}}, {'source': {'label': 'Hysterium', 'id': 'NCBITaxon:100026'}, 'relationship': 'biolink:subclass_of', 'target': {'label': 'Hysterium hyalinum', 'id': 'NCBITaxon:574776'}}, {'source': {'label': 'Hysterium', 'id': 'NCBITaxon:100026'}, 'relationship': 'biolink:subclass_of', 'target': {'label': 'unclassified Hysterium', 'id': 'NCBITaxon:2649321'}}, {'source': {'label': 'Hysterium', 'id': 'NCBITaxon:100026'}, 'relationship': 'biolink:subclass_of', 'target': {'label': 'Hysterium rhizophorae', 'id': 'NCBITaxon:2066082'}}, {'source': {'label': 'Hysterium', 'id': 'NCBITaxon:100026'}, 'relationship': 'biolink:subclass_of', 'target': {'label': 'Hysterium pulicare', 'id': 'NCBITaxon:100027'}}, {'source': {'label': 'Hysterium', 'id': 'NCBITaxon:100026'}, 'relationship': 'biolink:subclass_of', 'target': {'label': 'Hysteriaceae', 'id': 'NCBITaxon:100025'}}]}}]

    > Finished chain.
    <HTML representation of the KG>

