# kg-chat

Chatbot that looks up information from provided KGX files (nodes and edges TSV files)

## Requirements
- Neo4j Desktop

## Setup

1. Install Neo4j desktop from [here](https://neo4j.com/download/?utm_source=Google&utm_medium=PaidSearch&utm_campaign=Evergreen&utm_content=AMS-Search-SEMBrand-Evergreen-None-SEM-SEM-NonABM&utm_term=download%20neo4j&utm_adgroup=download&gad_source=1&gbraid=0AAAAADk9OYqwuLc9mMDBV2n4GXbXo8LzS&gclid=Cj0KCQjwv7O0BhDwARIsAC0sjWOzlSRw10D0r0jnxU2FtVs1MlC1lMVhl2GqH8pa4HAoaVS85DQO9nsaArSfEALw_wcB)

2. Create a new project by giving it a name of your choice
3. Create an empty database with a name of your choice and `Start` it.
    - Credentials can be as declared [here](https://github.com/hrshdhgd/kg-chat/blob/9ffd530e0da60da772403a327707fc3128d916e5/src/kg_chat/constants.py#L11-L12)
4. Clone this repository locally
5. Create a virtual environment of your choice and `pip install poetry` in it.
6. 
    ```shell
    cd kg-chat
    poetry install
    ```
8. replace the `data/nodes.tsv` and `data/edges.tsv` file in the project with analogous files of choice.
9. 
    ```shell
    kg-chat import-kg
    ```
    This loads the nodes and edges file into a Neo4j instance. This will take a while depending on the size of the tsv files.
10. To test that this worked, run the test query provided:
    ```shell
    kg-chat test-query
    ```
    This should return something like (as per data in the repo):
    ```shell
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
    ```

### Commands

1. `qna`:
    ```shell
    kg-chat qna "give me the sorted (descending) frequency count nodes with relationships. Give me label and id. I want this as a table "
    ```
    This should return
    ```shell
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
    ```

2. `start-chat`: This starts an interactive chat session where you can ask questions about your KG.
    ```shell
    kg-chat start-chat
    ```
    Gives you the following:
    ```shell
    Ask me about your data! : 
    ```
    You have to make sure the question is framed properly. As of now this errors out easily. To quit type `quit` or `exit`.

---
## Acknowledgements

This [cookiecutter](https://cookiecutter.readthedocs.io/en/stable/README.html) project was developed from the [monarch-project-template](https://github.com/monarch-initiative/monarch-project-template) template and will be kept up-to-date using [cruft](https://cruft.github.io/cruft/).
