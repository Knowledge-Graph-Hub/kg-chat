Setup
=====

.. note::

    Follow steps 1 through 5 **ONLY** if you want to work with Neo4j as the backend. If you intend to use just DuckDB feel free to skip these steps.

1. Install Neo4j desktop from `here <https://neo4j.com/download/?utm_source=Google&utm_medium=PaidSearch&utm_campaign=Evergreen&utm_content=AMS-Search-SEMBrand-Evergreen-None-SEM-SEM-NonABM&utm_term=download%20neo4j&utm_adgroup=download&gad_source=1&gbraid=0AAAAADk9OYqwuLc9mMDBV2n4GXbXo8LzS&gclid=Cj0KCQjwv7O0BhDwARIsAC0sjWOzlSRw10D0r0jnxU2FtVs1MlC1lMVhl2GqH8pa4HAoaVS85DQO9nsaArSfEALw_wcB>`_

2. Create a new project by giving it a name of your choice. Make sure to choose the latest version of Neo4j. At this time it is (v5.21.2).

3. Create an empty database with a name of your choice and ``Start`` it.
    - Credentials can be as declared `here <https://github.com/hrshdhgd/kg-chat/blob/9ffd530e0da60da772403a327707fc3128d916e5/src/kg_chat/constants.py#L11-L12>`_

4. Install the APOC plugin in Neo4j Desktop. It is listed under the ``Plugins`` tab which appears when you single-click the database.

5. Click on ``Settings`` which is visible when you click on the 3 dots that appears to the right of the db on single-clicking as well. It should match ``neo4j_db_settings.conf``

    The main edits you'll need to do are these 3 lines:
    
    .. code-block:: conf
    
        dbms.memory.heap.initial_size=1G
        dbms.memory.heap.max_size=16G
        dbms.security.procedures.allowlist=apoc.coll.*,apoc.load.*,gds.*,apoc.meta.data

    Update the memory heaps as per your preference.

6. Clone this repository locally

7. Create a virtual environment of your choice and ``pip install poetry`` in it.

8. 

    .. code-block:: shell

        cd kg-chat
        poetry install

9. Replace the ``data/nodes.tsv`` and ``data/edges.tsv`` file in the project with corresponding files of choice that needs to be queried against.
