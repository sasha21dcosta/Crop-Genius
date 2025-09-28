from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
import os
import pandas as pd
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from langdetect import detect, DetectorFactory
from transformers import pipeline
import re
import traceback

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_DIR = os.path.join(BASE_DIR, 'kb')
KB_CSV = os.path.join(KB_DIR, 'crop_disease_kb.csv')
EMBEDDINGS_PKL = os.path.join(KB_DIR, 'symptom_embeddings.pkl')

# Load KB and embeddings once
if not os.path.exists(KB_DIR):
    os.makedirs(KB_DIR)

def load_kb_and_embeddings():
    df = pd.read_csv(KB_CSV)
    with open(EMBEDDINGS_PKL, 'rb') as f:
        symptom_embeddings = pickle.load(f)
    return df, symptom_embeddings

df, symptom_embeddings = None, None
model = None
translator_hi_en = None
translator_mr_en = None
translator_en_hi = None
translator_en_mr = None

# Load everything on first import
try:
    df, symptom_embeddings = load_kb_and_embeddings()
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
except Exception as e:
    print('Error loading KB or embedding model:', e)
    traceback.print_exc()

# Load translation pipelines individually
try:
    translator_hi_en = pipeline('translation', model='Helsinki-NLP/opus-mt-hi-en')
except Exception as e:
    print('Error loading translator_hi_en:', e)
    traceback.print_exc()
    translator_hi_en = None
try:
    translator_mr_en = pipeline('translation', model='Helsinki-NLP/opus-mt-mr-en')
except Exception as e:
    print('Error loading translator_mr_en:', e)
    traceback.print_exc()
    translator_mr_en = None
try:
    translator_en_hi = pipeline('translation', model='Helsinki-NLP/opus-mt-en-hi')
except Exception as e:
    print('Error loading translator_en_hi:', e)
    traceback.print_exc()
    translator_en_hi = None
try:
    translator_en_mr = pipeline('translation', model='Helsinki-NLP/opus-mt-en-mr')
except Exception as e:
    print('Error loading translator_en_mr:', e)
    traceback.print_exc()
    translator_en_mr = None

def cosine_sim_vectorized(matrix, vector):
    norm_matrix = np.linalg.norm(matrix, axis=1)
    norm_vector = np.linalg.norm(vector)
    return np.dot(matrix, vector) / (norm_matrix * norm_vector)

# Add a helper to check for code-mixing
def is_code_mixed(text):
    # Simple heuristic: presence of both Devanagari and Latin characters
    devanagari = re.search(r'[\u0900-\u097F]', text)
    latin = re.search(r'[A-Za-z]', text)
    return bool(devanagari and latin)

class DetectDiseaseView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        global df, symptom_embeddings, model
        data = request.data
        input_text = data.get('symptom_text', '')
        crop = data.get('crop', '').lower()  # Get selected crop
        followup_choice = data.get('followup_choice', None)
        
        # Filter KB by selected crop
        if crop and crop in ['rice', 'wheat', 'apple', 'tomato', 'potato']:
            crop_df = df[df['crop'].str.lower() == crop].copy()
            if crop_df.empty:
                return Response({'error': f'No disease data available for {crop}'}, status=400)
        else:
            return Response({'error': 'Please select a valid crop'}, status=400)
        user_lang = None
        translated = False
        translated_text = input_text
        # 1. Detect language
        try:
            user_lang = detect(input_text)
        except Exception:
            user_lang = 'en'
        # 2. Translate if needed (handle code-mixed)
        if user_lang in ['hi', 'mr'] or is_code_mixed(input_text):
            # Prefer Hindi if code-mixed, fallback to Marathi
            if user_lang == 'mr':
                if not translator_mr_en:
                    return Response({'error': 'Marathi-English translation model not available.'}, status=500)
                translated_text = translator_mr_en(input_text)[0]['translation_text']
            else:
                if not translator_hi_en:
                    return Response({'error': 'Hindi-English translation model not available.'}, status=500)
                translated_text = translator_hi_en(input_text)[0]['translation_text']
            translated = True
        # 3. Create crop-specific embeddings
        crop_symptoms = crop_df['symptom_description'].tolist()
        crop_embeddings = model.encode(crop_symptoms)
        
        # 4. Calculate similarity with crop-specific data
        input_emb = model.encode([translated_text])[0]
        sims = cosine_sim_vectorized(crop_embeddings, input_emb)
        top_k = 5
        top_indices = np.argsort(sims)[-top_k:][::-1]
        top_scores = sims[top_indices]
        confidence_threshold = 0.55  # Lower threshold for crop-specific detection
        # Aggregate top candidate diseases (using crop-specific data)
        candidate_map = {}
        for idx, score in zip(top_indices, top_scores):
            if idx < 0 or idx >= len(crop_df):
                continue
            row = crop_df.iloc[idx]
            disease = row['disease_name']
            if disease not in candidate_map:
                candidate_map[disease] = {
                    'disease_name': disease,
                    'crop': row['crop'],
                    'symptoms': set(),
                    'treatments': set(),
                    'preventions': set(),
                    'indices': [],
                    'max_score': float(score),
                    'avg_score': [],
                }
            candidate_map[disease]['symptoms'].add(row['symptom_description'])
            candidate_map[disease]['treatments'].add(row['treatment'])
            candidate_map[disease]['preventions'].add(row['prevention'])
            candidate_map[disease]['indices'].append(idx)
            candidate_map[disease]['avg_score'].append(float(score))
            if float(score) > candidate_map[disease]['max_score']:
                candidate_map[disease]['max_score'] = float(score)
        # Prepare ranked candidates
        candidates = list(candidate_map.values())
        for c in candidates:
            c['avg_score'] = float(np.mean(c['avg_score']))
            c['symptoms'] = list(c['symptoms'])
            c['treatments'] = list(c['treatments'])
            c['preventions'] = list(c['preventions'])
        candidates = sorted(candidates, key=lambda x: x['avg_score'], reverse=True)
        # If followup_choice is provided, use it to refine prediction
        if followup_choice is not None:
            try:
                idx = int(followup_choice)
                if idx < 0 or idx >= len(top_indices):
                    return Response({'error': 'No matching row found.'}, status=400)
                best_match_idx = top_indices[idx]
                if best_match_idx < 0 or best_match_idx >= len(crop_df):
                    return Response({'error': 'No matching row found.'}, status=400)
            except Exception:
                best_match_idx = top_indices[0]
            row = crop_df.iloc[best_match_idx]
            result = {
                'final_prediction': {
                    'disease_name': row['disease_name'],
                    'crop': row['crop'],
                    'matched_symptom': row['symptom_description'],
                    'treatment': row['treatment'],
                    'prevention': row['prevention'],
                    'confidence': float(sims[best_match_idx]),
                },
                'candidates': candidates,
                'input_language': user_lang,
                'translated_text': translated_text if translated else None,
                'used_followup': True
            }
            # Optionally translate advice back
            if translated:
                if (user_lang == 'hi' or (user_lang != 'mr' and is_code_mixed(input_text))):
                    if not translator_en_hi:
                        return Response({'error': 'English-Hindi translation model not available.'}, status=500)
                    result['final_prediction']['treatment'] = translator_en_hi(result['final_prediction']['treatment'])[0]['translation_text']
                    result['final_prediction']['prevention'] = translator_en_hi(result['final_prediction']['prevention'])[0]['translation_text']
                elif user_lang == 'mr':
                    if not translator_en_mr:
                        return Response({'error': 'English-Marathi translation model not available.'}, status=500)
                    result['final_prediction']['treatment'] = translator_en_mr(result['final_prediction']['treatment'])[0]['translation_text']
                    result['final_prediction']['prevention'] = translator_en_mr(result['final_prediction']['prevention'])[0]['translation_text']
            return Response(result)
        # If confidence is low, ask follow-up questions
        if float(top_scores[0]) < confidence_threshold:
            followup_questions = []
            for i, idx in enumerate(top_indices):
                if idx < 0 or idx >= len(crop_df):
                    continue
                desc = crop_df.iloc[idx]['symptom_description']
                followup_questions.append(f"{i+1}. {desc}")
            question_text = (
                f"I'm analyzing your {crop} symptoms but need more details for accurate diagnosis.\n" +
                "Which of these symptoms best matches what you see on your crop?\n" +
                "\n".join(followup_questions[:3])  # Limit to top 3 for clarity
            )
            return Response({
                'need_followup': True,
                'candidates': candidates,
                'followup_questions': followup_questions,
                'message': question_text,
                'input_language': user_lang,
                'translated_text': translated_text if translated else None
            })
        # Normal confident prediction
        best_candidate = candidates[0]
        result = {
            'final_prediction': {
                'disease_name': best_candidate['disease_name'],
                'crop': best_candidate['crop'],
                'matched_symptom': best_candidate['symptoms'][0],
                'treatment': best_candidate['treatments'][0],
                'prevention': best_candidate['preventions'][0],
                'confidence': best_candidate['avg_score'],
            },
            'candidates': candidates,
            'input_language': user_lang,
            'translated_text': translated_text if translated else None,
            'used_followup': False
        }
        # Optionally translate advice back
        if translated:
            if (user_lang == 'hi' or (user_lang != 'mr' and is_code_mixed(input_text))):
                if not translator_en_hi:
                    return Response({'error': 'English-Hindi translation model not available.'}, status=500)
                result['final_prediction']['treatment'] = translator_en_hi(result['final_prediction']['treatment'])[0]['translation_text']
                result['final_prediction']['prevention'] = translator_en_hi(result['final_prediction']['prevention'])[0]['translation_text']
            elif user_lang == 'mr':
                if not translator_en_mr:
                    return Response({'error': 'English-Marathi translation model not available.'}, status=500)
                result['final_prediction']['treatment'] = translator_en_mr(result['final_prediction']['treatment'])[0]['translation_text']
                result['final_prediction']['prevention'] = translator_en_mr(result['final_prediction']['prevention'])[0]['translation_text']
        return Response(result)
