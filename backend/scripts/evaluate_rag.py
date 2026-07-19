import os
import sys
import json
import asyncio
import time
from tabulate import tabulate
from dotenv import load_dotenv

# Ensure the backend directory is in the path so imports work
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.rag.pipeline import rag_pipeline
from app.vectorstore.pinecone_store import vector_store_manager

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

async def evaluate():
    dataset_path = os.path.join(os.path.dirname(__file__), 'ground_truth.json')
    if not os.path.exists(dataset_path):
        print("Dataset not found. Please run generate_ground_truth.py first.")
        return
        
    with open(dataset_path, 'r') as f:
        dataset = json.load(f)
        
    print(f"Loaded {len(dataset)} evaluation questions.")
    
    # Configuration to test
    top_k = 20
    # Use a dummy project ID that contains the ingested document
    # For a real automated test, we would ingest a document into a temp project here.
    # To keep it simple, we assume the user has already ingested the NodeJS doc in their active project.
    # But to be perfectly empirical, let's ingest it into a test project.
    
    test_project_id = "eval_project_001"
    
    # 1. Ingest Data for Evaluation
    from generate_ground_truth import get_text_from_url
    TEST_URL = "https://nodejs.org/docs/latest/api/cluster.html"
    print(f"Ingesting {TEST_URL} into test vector space ({test_project_id})...")
    text = get_text_from_url(TEST_URL)
    rag_pipeline.process_document(test_project_id, text, TEST_URL, chunk_size=1000, chunk_overlap=200)
    
    # Give Pinecone a few seconds to index
    print("Waiting 10 seconds for vector index to settle...")
    time.sleep(10)
    
    # 2. Run Evaluation
    print(f"Running evaluation with top_k={top_k}...")
    store = vector_store_manager.get_store(test_project_id)
    
    hits = 0
    mrr_sum = 0
    
    results = []
    
    for item in dataset:
        question = item['question']
        ground_truth = item['ground_truth_chunk']
        
        # We only need the retrieval step, not the full LLM generation
        docs = await asyncio.to_thread(store.similarity_search, question, k=top_k)
        
        # Check if ground truth is in retrieved docs
        # We check substring because chunking might overlap or differ slightly
        rank = 0
        hit = False
        for i, doc in enumerate(docs):
            # A simple heuristic: if 80% of the retrieved text is in the ground truth, it's a hit
            # Or simpler: if the retrieved chunk contains a significant portion of the ground truth
            if doc.page_content.strip()[:100] in ground_truth or ground_truth[:100] in doc.page_content:
                rank = i + 1
                hit = True
                break
                
        if hit:
            hits += 1
            mrr_sum += 1 / rank
            results.append({"Q": question[:30]+"...", "Hit": "Yes", "Rank": rank})
        else:
            results.append({"Q": question[:30]+"...", "Hit": "No", "Rank": "-"})
            
    # Calculate metrics
    total = len(dataset)
    hit_rate = (hits / total) * 100
    mrr = mrr_sum / total
    
    print("\n" + "="*50)
    print("RAG EVALUATION REPORT")
    print("="*50)
    print(tabulate(results, headers="keys", tablefmt="grid"))
    print("\nMetrics:")
    print(f"Total Questions: {total}")
    print(f"Top-{top_k} Hit Rate: {hit_rate:.2f}% (Higher is better)")
    print(f"Mean Reciprocal Rank (MRR): {mrr:.4f} (Higher is better, Max 1.0)")
    
    print("\nEvaluation complete.")

if __name__ == "__main__":
    asyncio.run(evaluate())
