import pandas as pd
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_CSV = os.path.join(BASE_DIR, 'crop_disease_kb.csv')
EMBEDDINGS_PKL = os.path.join(BASE_DIR, 'symptom_embeddings.pkl')

model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
df = pd.read_csv(KB_CSV)
symptom_texts = df['symptom_description'].tolist()
symptom_embeddings = model.encode(symptom_texts)

with open(EMBEDDINGS_PKL, 'wb') as f:
    pickle.dump(symptom_embeddings, f)

print('Embeddings generated and saved to', EMBEDDINGS_PKL)
