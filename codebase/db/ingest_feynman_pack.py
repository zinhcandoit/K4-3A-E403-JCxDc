import os
import sys
from falkordb import FalkorDB

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from config.config import settings
from db.data_loader import RealDataLoader

FALKOR_HOST = settings.FALKOR_HOST
FALKOR_PORT = settings.FALKOR_PORT
GRAPH_NAME = settings.GRAPH_NAME


def _sanitize_cypher(value: str) -> str:
    """Escape single and double quotes for safe Cypher query interpolation."""
    return str(value or "").replace("'", "\\'").replace('"', '\\"')


def ingest_vlearn_feynman_knowledge():
    """
    Ingest curriculum concepts parsed from transcript files into FalkorDB Primary Track.
    Maintains zero data leakage with dynamic ingestion.
    """
    print(f"📦 Connecting to FalkorDB at {FALKOR_HOST}:{FALKOR_PORT}...")
    db_client = FalkorDB(host=FALKOR_HOST, port=FALKOR_PORT)
    graph = db_client.select_graph(GRAPH_NAME)
    try:
        graph.delete()
        print("🗑️ Reset existing graph for fresh curriculum ingestion...")
    except Exception:
        pass
    graph = db_client.select_graph(GRAPH_NAME)

    loader = RealDataLoader()
    feynman_curriculum = loader.parse_vlearn_transcripts()

    # Ingest concepts with dual labeling (:Concept:FeynmanConcept)
    for index, concept_item in enumerate(feynman_curriculum):
        safe_quote = _sanitize_cypher(concept_item.get("quote_text", ""))
        safe_truth = _sanitize_cypher(concept_item.get("core_truth", ""))
        safe_question = _sanitize_cypher(concept_item.get("learning_question") or concept_item.get("child_question", ""))
        safe_name = _sanitize_cypher(concept_item.get("name", ""))
        safe_module = _sanitize_cypher(concept_item.get("module", "VLearn Foundation"))

        # Clean existing nodes if present
        graph.query(f"MATCH (fc:FeynmanConcept {{id: '{concept_item['id']}'}}) DELETE fc")
        graph.query(f"MATCH (c:Concept {{id: '{concept_item['id']}'}}) DELETE c")

        query = f"""
        CREATE (c:Concept:FeynmanConcept {{
            id: '{concept_item["id"]}',
            name: '{safe_name}',
            category: 'Feynman VLearn Pack',
            module: '{safe_module}',
            page: {index + 1},
            order: {index + 1},
            summary: '{safe_truth}',
            track: 'primary',
            status: 'UNCOVERED',
            citation: '{concept_item["citation"]}',
            core_truth: '{safe_truth}',
            quote_text: '{safe_quote}',
            child_question: '{safe_question}',
            learning_question: '{safe_question}'
        }})
        """
        graph.query(query)

    # Establish linear PREREQUISITE_FOR relationships in Primary Track
    for step_index in range(len(feynman_curriculum) - 1):
        current_id = feynman_curriculum[step_index]["id"]
        next_id = feynman_curriculum[step_index + 1]["id"]
        graph.query(f"""
        MATCH (a:Concept {{id: '{current_id}'}}), (b:Concept {{id: '{next_id}'}})
        MERGE (a)-[:PREREQUISITE_FOR]->(b)
        """)

    print("🎉 Successfully ingested curriculum concepts into FalkorDB Primary Track.")
    query_result = graph.query("MATCH (c:Concept {track: 'primary'}) RETURN c.id, c.name, c.citation, c.order ORDER BY c.order")
    for record in query_result.result_set:
        print(f"🔹 [{record[2]}] #{record[3]} {record[1]} (ID: {record[0]})")


if __name__ == "__main__":
    ingest_vlearn_feynman_knowledge()
