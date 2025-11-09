"""
Script to generate embeddings from the new JSON knowledge base format.
Run this after updating crop_disease_kb.json
"""

import os
import json
import pickle
from sentence_transformers import SentenceTransformer

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_JSON = os.path.join(BASE_DIR, 'crop_disease_kb.json')
EMBEDDINGS_PKL = os.path.join(BASE_DIR, 'symptom_embeddings_new.pkl')

def generate_embeddings():
    print("Loading knowledge base...")
    with open(KB_JSON, 'r', encoding='utf-8') as f:
        diseases = json.load(f)
    
    print(f"Loaded {len(diseases)} disease entries")
    
    print("Loading embedding model...")
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    
    print("Generating embeddings for EACH symptom...")
    embeddings_data = []
    
    for disease in diseases:
        # Create ONE embedding PER symptom for better matching
        for symptom in disease['symptoms']:
            # Generate embedding for this specific symptom
            embedding = model.encode(symptom)
            
            embeddings_data.append({
                'crop_name': disease['crop_name'],
                'disease_name': disease['disease_name'],
                'symptom_text': symptom,  # Individual symptom
                'embedding': embedding,
                'full_data': disease  # Store full disease data for easy access
            })
        
        print(f"  ✓ {disease['crop_name']} - {disease['disease_name']} ({len(disease['symptoms'])} symptoms)")
    
    print(f"\nSaving embeddings to {EMBEDDINGS_PKL}...")
    with open(EMBEDDINGS_PKL, 'wb') as f:
        pickle.dump(embeddings_data, f)
    
    print("✅ Embeddings generated successfully!")
    print(f"Total embeddings: {len(embeddings_data)} (one per symptom)")

if __name__ == '__main__':
    generate_embeddings()

