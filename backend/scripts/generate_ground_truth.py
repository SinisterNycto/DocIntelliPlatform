import os
import json
import random
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai
from langchain_text_splitters import MarkdownTextSplitter

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

def gemini_client():
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def get_text_from_url(url):
    print(f"Fetching {url}...")
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.decompose()
    return soup.get_text(separator=' ', strip=True)

def generate_questions(text, num_questions=10):
    print("Chunking text...")
    splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=0)
    chunks = splitter.split_text(text)
    
    # Randomly sample chunks to generate questions
    sampled_chunks = random.sample(chunks, min(num_questions, len(chunks)))
    
    dataset = []
    print(f"Generating {len(sampled_chunks)} questions using Gemini...")
    for i, chunk in enumerate(sampled_chunks):
        prompt = f"""
        You are an evaluator. Given the following context block, generate EXACTLY ONE specific question that can ONLY be answered by this context block.
        The question should be concise. Do not include any other text, just the question.
        
        Context Block:
        {chunk}
        """
        try:
            model_name = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
            response = gemini_client().models.generate_content(model=model_name, contents=prompt)
            question = (response.text or "").strip()
            if question:
                dataset.append({
                    "id": i,
                    "question": question,
                    "ground_truth_chunk": chunk
                })
                print(f"[{i+1}/{len(sampled_chunks)}] Generated Q: {question}")
        except Exception as e:
            print(f"Failed to generate question: {e}")
            
    return dataset

if __name__ == "__main__":
    # We use a sample documentation URL to build the dataset
    TEST_URL = "https://nodejs.org/docs/latest/api/cluster.html"
    
    text = get_text_from_url(TEST_URL)
    dataset = generate_questions(text, num_questions=15)
    
    output_path = os.path.join(os.path.dirname(__file__), 'ground_truth.json')
    with open(output_path, 'w') as f:
        json.dump(dataset, f, indent=4)
    
    print(f"Saved {len(dataset)} evaluation pairs to {output_path}")
