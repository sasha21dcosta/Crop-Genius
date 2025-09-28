#!/usr/bin/env python3
"""
Script to regenerate embeddings for the crop disease knowledge base.
Run this whenever the KB CSV is updated.
"""

import os
import pandas as pd
import pickle
from sentence_transformers import SentenceTransformer

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_DIR = os.path.join(BASE_DIR, 'kb')
KB_CSV = os.path.join(KB_DIR, 'crop_disease_kb.csv')
EMBEDDINGS_PKL = os.path.join(KB_DIR, 'symptom_embeddings.pkl')

def main():
    print("Loading knowledge base...")
    df = pd.read_csv(KB_CSV)
    print(f"Loaded {len(df)} records from KB")
    
    print("Loading SentenceTransformer model...")
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    
    print("Generating embeddings for symptom descriptions...")
    symptoms = df['symptom_description'].tolist()
    embeddings = model.encode(symptoms, show_progress_bar=True)
    
    print(f"Generated {len(embeddings)} embeddings")
    print(f"Embedding shape: {embeddings.shape}")
    
    print("Saving embeddings...")
    with open(EMBEDDINGS_PKL, 'wb') as f:
        pickle.dump(embeddings, f)
    
    print(f"Embeddings saved to {EMBEDDINGS_PKL}")
    print("Done!")

if __name__ == '__main__':
    main()
