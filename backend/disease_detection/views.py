from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
import os
import pandas as pd
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from langdetect import detect, DetectorFactory
from transformers import pipeline
import re
import traceback
import tempfile
from rest_framework.parsers import MultiPartParser, FormParser
import requests
from .models import ChatSession, ChatMessage
from django.shortcuts import get_object_or_404

COLAB_API_URL = "https://26954b8d4135.ngrok-free.app"  # UPDATE with your own Colab ngrok URL (no /api/transcribe suffix)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_DIR = os.path.join(BASE_DIR, 'kb')
KB_JSON = os.path.join(KB_DIR, 'crop_disease_kb.json')
EMBEDDINGS_PKL = os.path.join(KB_DIR, 'symptom_embeddings_new.pkl')

# Load KB and embeddings once
if not os.path.exists(KB_DIR):
    os.makedirs(KB_DIR)

def load_kb_and_embeddings():
    import json
    with open(KB_JSON, 'r', encoding='utf-8') as f:
        diseases = json.load(f)
    with open(EMBEDDINGS_PKL, 'rb') as f:
        embeddings_data = pickle.load(f)
    return diseases, embeddings_data

diseases_kb, embeddings_data = None, None
model = None
translator_hi_en = None
translator_mr_en = None
translator_en_hi = None
translator_en_mr = None

# Load everything on first import
try:
    diseases_kb, embeddings_data = load_kb_and_embeddings()
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    print(f"✅ Loaded {len(diseases_kb)} diseases and {len(embeddings_data)} embeddings")
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
        global diseases_kb, embeddings_data, model
        data = request.data
        input_text = data.get('symptom_text', '')
        crop = data.get('crop', '').lower()
        action = data.get('action', None)  # For conversational actions (Stage 2)
        disease_name = data.get('disease_name', None)  # For action-based requests
        followup_answer = data.get('followup_answer', None)  # User's symptom selection
        
        # Filter embeddings by selected crop
        if not crop or crop not in ['rice', 'wheat', 'apple', 'tomato', 'potato']:
            return Response({'error': 'Please select a valid crop'}, status=400)
        
        crop_embeddings_list = [e for e in embeddings_data if e['crop_name'].lower() == crop]
        if not crop_embeddings_list:
            return Response({'error': f'No disease data available for {crop}'}, status=400)
        
        # STAGE 2: Handle action-based requests (ONLY after disease confirmed)
        if action and disease_name:
            return self._handle_action(action, disease_name, crop)
        
        # STAGE 1: Disease Detection & Confirmation
        
        # Language detection and translation
        user_lang = 'en'
        translated = False
        translated_text = input_text
        
        try:
            user_lang = detect(input_text)
        except Exception:
            user_lang = 'en'
        
        if user_lang in ['hi', 'mr'] or is_code_mixed(input_text):
            if user_lang == 'mr' and translator_mr_en:
                translated_text = translator_mr_en(input_text)[0]['translation_text']
                translated = True
            elif translator_hi_en:
                translated_text = translator_hi_en(input_text)[0]['translation_text']
                translated = True
        
        # If user provided followup answer (selected a symptom from clarification)
        if followup_answer is not None and input_text:
            try:
                selected_idx = int(followup_answer)
                
                # Re-run the similarity to get top 3 diseases
                input_emb = model.encode([translated_text if translated else input_text])[0]
                crop_embeddings_matrix = np.array([e['embedding'] for e in crop_embeddings_list])
                sims = cosine_sim_vectorized(crop_embeddings_matrix, input_emb)
                
                # Aggregate by disease
                disease_scores = {}
                for idx, score in enumerate(sims):
                    disease_name = crop_embeddings_list[idx]['disease_name']
                    if disease_name not in disease_scores:
                        disease_scores[disease_name] = {
                            'max_score': float(score),
                            'data': crop_embeddings_list[idx]['full_data']
                        }
                    if float(score) > disease_scores[disease_name]['max_score']:
                        disease_scores[disease_name]['max_score'] = float(score)
                
                ranked_diseases = sorted(
                    disease_scores.items(),
                    key=lambda x: x[1]['max_score'],
                    reverse=True
                )
                top_3_diseases = ranked_diseases[:3]
                
                # Collect symptoms shown to user (same logic as clarification)
                followup_options = []
                disease_for_symptom = []
                
                for disease_name, info in top_3_diseases:
                    symptoms = info['data'].get('symptoms', [])[:2]
                    for symptom in symptoms:
                        if symptom not in followup_options:
                            followup_options.append(symptom)
                            disease_for_symptom.append(info['data'])
                
                # User selected one of these symptoms - find the corresponding disease
                if 0 <= selected_idx < len(disease_for_symptom):
                    best_disease_data = disease_for_symptom[selected_idx]
                    best_score = 0.95  # User confirmed, high confidence
                    
                    print(f"✅ User selected symptom #{selected_idx}: Confirmed {best_disease_data['disease_name']}")
                    
                    # Return FINAL diagnosis with conversational actions
                    return self._return_final_diagnosis(best_disease_data, best_score, user_lang, translated)
            except Exception as e:
                print(f"Error processing followup answer: {e}")
        
        # Calculate similarities with ALL symptoms for selected crop
        input_emb = model.encode([translated_text])[0]
        crop_embeddings_matrix = np.array([e['embedding'] for e in crop_embeddings_list])
        sims = cosine_sim_vectorized(crop_embeddings_matrix, input_emb)
        
        # Aggregate scores by disease (since we have multiple symptoms per disease)
        disease_scores = {}
        for idx, score in enumerate(sims):
            disease_name = crop_embeddings_list[idx]['disease_name']
            
            if disease_name not in disease_scores:
                disease_scores[disease_name] = {
                    'scores': [],
                    'max_score': float(score),
                    'data': crop_embeddings_list[idx]['full_data'],
                    'best_symptom_idx': idx
                }
            
            disease_scores[disease_name]['scores'].append(float(score))
            if float(score) > disease_scores[disease_name]['max_score']:
                disease_scores[disease_name]['max_score'] = float(score)
                disease_scores[disease_name]['best_symptom_idx'] = idx
        
        # Calculate average score for each disease
        for disease_name in disease_scores:
            scores = disease_scores[disease_name]['scores']
            disease_scores[disease_name]['avg_score'] = float(np.mean(scores))
        
        # Rank diseases by max score (best symptom match)
        ranked_diseases = sorted(
            disease_scores.items(), 
            key=lambda x: x[1]['max_score'],  # Sort by best symptom match
            reverse=True
        )
        
        # Get top 3 diseases
        top_3_diseases = ranked_diseases[:3]
        best_disease_name = top_3_diseases[0][0]
        best_score = top_3_diseases[0][1]['max_score']
        best_disease_data = top_3_diseases[0][1]['data']
        best_symptom_idx = top_3_diseases[0][1]['best_symptom_idx']
        matched_symptom = crop_embeddings_list[best_symptom_idx]['symptom_text']
        
        print(f"\n🔍 DIAGNOSIS ANALYSIS:")
        print(f"User input: '{input_text}' (translated: '{translated_text}')")
        print(f"Crop: {crop}")
        print(f"\nTop 3 Diseases:")
        for i, (disease_name, info) in enumerate(top_3_diseases, 1):
            symptom_match = crop_embeddings_list[info['best_symptom_idx']]['symptom_text']
            print(f"  {i}. {disease_name}: {info['max_score']:.3f} (avg: {info['avg_score']:.3f})")
            print(f"      Best matching symptom: '{symptom_match}'")
        print(f"\nBest match: {best_disease_name} with {best_score:.2%} confidence")
        print(f"Matched symptom: '{matched_symptom}'\n")
        
        # Confidence threshold
        confidence_threshold = 0.60
        
        # Count how many diseases are above threshold
        diseases_above_threshold = [
            (name, info) for name, info in top_3_diseases 
            if info['max_score'] >= confidence_threshold
        ]
        
        print(f"Diseases above {confidence_threshold:.0%} threshold: {len(diseases_above_threshold)}")
        for name, info in diseases_above_threshold:
            print(f"  - {name}: {info['max_score']:.2%}")
        
        # AMBIGUOUS: Multiple diseases above threshold - need clarification
        if len(diseases_above_threshold) > 1:
            print("⚠️ Multiple diseases above threshold - asking follow-up questions\n")
            followup_options = []
            diseases_considered = []
            
            # Collect highly matched symptoms ONLY from diseases above threshold
            for disease_name, info in diseases_above_threshold:
                if disease_name not in diseases_considered:
                    diseases_considered.append(disease_name)
                    
                    # Get the TOP matching symptoms for this disease (the ones that scored high)
                    # Find all symptoms for this disease with their scores
                    disease_symptom_scores = []
                    for idx, score in enumerate(sims):
                        if crop_embeddings_list[idx]['disease_name'] == disease_name:
                            disease_symptom_scores.append({
                                'symptom': crop_embeddings_list[idx]['symptom_text'],
                                'score': float(score),
                                'idx': idx
                            })
                    
                    # Sort by score and take top 2-3 symptoms
                    disease_symptom_scores.sort(key=lambda x: x['score'], reverse=True)
                    top_symptoms = disease_symptom_scores[:2]  # Top 2 symptoms per disease
                    
                    print(f"  Showing top symptoms for {disease_name}:")
                    for s in top_symptoms:
                        print(f"    - {s['symptom']} ({s['score']:.2%})")
                        if s['symptom'] not in followup_options:
                            followup_options.append(s['symptom'])
            
            # Limit to 6 options max for better UX
            followup_options = followup_options[:6]
            
            message = f"🤔 I found {len(diseases_considered)} possible diseases for your {crop}:\n\n"
            message += f"Top matches: {', '.join(diseases_considered)}\n\n"
            message += f"To give you accurate diagnosis, which of these symptoms BEST matches what you see?"
            
            return Response({
                'type': 'clarification_needed',
                'message': message,
                'followup_questions': followup_options,
                'need_followup': True,
                'candidates': [
                    {
                        'disease_name': disease_name,
                        'confidence': float(info['max_score'])
                    }
                    for disease_name, info in diseases_above_threshold
                ],
                'input_language': user_lang,
                'translated': translated
            })
        
        # LOW CONFIDENCE: All diseases below threshold - ask follow-up from all top 3
        if best_score < confidence_threshold:
            print("⚠️ Low confidence - asking follow-up questions from all top 3\n")
            followup_options = []
            diseases_considered = []
            
            for disease_name, info in top_3_diseases:
                if disease_name not in diseases_considered:
                    diseases_considered.append(disease_name)
                    symptoms = info['data'].get('symptoms', [])[:2]
                    for symptom in symptoms:
                        if symptom not in followup_options:
                            followup_options.append(symptom)
            
            followup_options = followup_options[:6]
            
            message = f"🤔 I'm not very confident about the diagnosis.\n\n"
            message += f"Possible diseases: {', '.join(diseases_considered)}\n\n"
            message += f"Please select the symptom that BEST describes your crop:"
            
            return Response({
                'type': 'clarification_needed',
                'message': message,
                'followup_questions': followup_options,
                'need_followup': True,
                'candidates': [
                    {
                        'disease_name': disease_name,
                        'confidence': float(info['max_score'])
                    }
                    for disease_name, info in top_3_diseases
                ],
                'input_language': user_lang,
                'translated': translated
            })
        
        # HIGH CONFIDENCE: Return final diagnosis with conversational actions
        return self._return_final_diagnosis(best_disease_data, best_score, user_lang, translated, matched_symptom)
    
    def _return_final_diagnosis(self, disease_data, confidence, user_lang, translated, matched_symptom=None):
        """Return confirmed diagnosis with conversational action buttons"""
        severity = disease_data.get('severity_level', 'Medium')
        
        # Build diagnosis message
        diagnosis_msg = f"🔍 Diagnosis Confirmed!\n\n"
        diagnosis_msg += f"🦠 Disease: {disease_data['disease_name']}\n"
        diagnosis_msg += f"📊 Confidence: {int(confidence * 100)}%\n"
        diagnosis_msg += f"⚠️ Severity: {severity}\n"
        
        if matched_symptom:
            diagnosis_msg += f"✓ Matched: {matched_symptom}\n"
        
        diagnosis_msg += "\nWhat would you like to know?"
        
        # Quick action buttons (ONLY shown after disease is confirmed)
        quick_actions = [
            {'label': '💊 Treatment', 'action': 'treatment'},
            {'label': '🛡️ Prevention', 'action': 'prevention'},
            {'label': '📚 Learn More', 'action': 'learn_more'},
            {'label': '❓ Ask Questions', 'action': 'ask_questions'}
        ]
        
        return Response({
            'type': 'diagnosis',
            'message': diagnosis_msg,
            'disease_identified': {
                'disease_name': disease_data['disease_name'],
                'crop': disease_data['crop_name'],
                'confidence': confidence,
                'severity': severity,
                'risk_season': disease_data.get('risk_season', 'Unknown'),
                'matched_symptom': matched_symptom,
            },
            'quick_actions': quick_actions,
            'conversation_state': 'diagnosis_confirmed',
            'input_language': user_lang,
            'translated': translated
        })
    
    def _handle_action(self, action, disease_name, crop):
        """Handle conversational action requests"""
        # Find the disease data
        disease_data = None
        for disease in diseases_kb:
            if (disease['disease_name'].lower() == disease_name.lower() and 
                disease['crop_name'].lower() == crop.lower()):
                disease_data = disease
                break
        
        if not disease_data:
            return Response({'error': 'Disease not found'}, status=404)
        
        if action == 'treatment':
            msg = f"💊 Treatment for {disease_data['disease_name']}:\n\n"
            msg += f"{disease_data['treatment']}\n\n"
            msg += "Need more help?"
            
            actions = [
                {'label': '🛡️ Prevention Tips', 'action': 'prevention'},
                {'label': '❓ FAQs', 'action': 'ask_questions'},
                {'label': '✅ Got it', 'action': 'done'}
            ]
            
            return Response({
                'type': 'action_response',
                'message': msg,
                'quick_actions': actions,
                'conversation_state': 'treatment_shown'
            })
        
        elif action == 'prevention':
            msg = f"🛡️ Prevention Tips for {disease_data['disease_name']}:\n\n"
            msg += f"{disease_data['prevention']}\n\n"
            msg += "Stay proactive to keep your crops healthy!"
            
            actions = [
                {'label': '💊 Show Treatment', 'action': 'treatment'},
                {'label': '📚 Learn More', 'action': 'learn_more'},
                {'label': '✅ Thanks!', 'action': 'done'}
            ]
            
            return Response({
                'type': 'action_response',
                'message': msg,
                'quick_actions': actions,
                'conversation_state': 'prevention_shown'
            })
        
        elif action == 'learn_more':
            msg = f"📚 About {disease_data['disease_name']}:\n\n"
            msg += f"🔬 Causes:\n{disease_data['causes']}\n\n"
            msg += f"🌡️ Risk Season:\n{disease_data['risk_season']}\n\n"
            msg += f"🎯 Affected Parts:\n{', '.join(disease_data.get('affected_parts', ['Various parts']))}"
            
            actions = [
                {'label': '💊 Treatment', 'action': 'treatment'},
                {'label': '🛡️ Prevention', 'action': 'prevention'},
                {'label': '✅ Got it', 'action': 'done'}
            ]
            
            return Response({
                'type': 'action_response',
                'message': msg,
                'quick_actions': actions,
                'conversation_state': 'details_shown'
            })
        
        elif action == 'ask_questions':
            questions = disease_data.get('symptom_questions', [])
            followups = disease_data.get('contextual_followups', [])
            
            msg = f"❓ Questions about {disease_data['disease_name']}:\n\n"
            msg += "Symptom Check:\n"
            for i, q in enumerate(questions[:3], 1):
                msg += f"{i}. {q}\n"
            
            if followups:
                msg += "\n🌾 Context Questions:\n"
                for i, q in enumerate(followups[:2], 1):
                    msg += f"{i}. {q}\n"
            
            actions = [
                {'label': '💊 Treatment', 'action': 'treatment'},
                {'label': '🛡️ Prevention', 'action': 'prevention'},
                {'label': '✅ Done', 'action': 'done'}
            ]
            
            return Response({
                'type': 'action_response',
                'message': msg,
                'quick_actions': actions,
                'conversation_state': 'questions_shown'
            })
        
        elif action == 'done':
            msg = "✅ Great! Feel free to start a new diagnosis anytime.\n\n"
            msg += "💡 Tip: Regular monitoring helps catch diseases early!"
            
            return Response({
                'type': 'conversation_end',
                'message': msg,
                'conversation_state': 'completed'
            })
        
        return Response({'error': 'Unknown action'}, status=400)

class TranscribeAudioView(APIView):
    """
    Transcribe audio using Colab (Whisper + Ollama combined pipeline)
    Colab handles both transcription and translation to English
    """
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        audio_file = request.FILES.get('audio')
        if not audio_file or not audio_file.name:
            return Response({"error": "No audio file provided."}, status=400)
        
        try:
            # Send audio to Colab's combined Whisper + Ollama endpoint
            files = {"audio": (audio_file.name, audio_file, audio_file.content_type)}
            resp = requests.post(
                f"{COLAB_API_URL}/api/transcribe", 
                files=files, 
                timeout=120
            )
            
            if resp.status_code == 200:
                data = resp.json()
                
                # Extract response from Colab
                original_transcript = data.get('transcript', '').strip()
                translated_text = data.get('translated', original_transcript).strip()
                detected_language = data.get('detected_language', 'unknown')
                translation_applied = data.get('translation_applied', False)
                
                print(f"[COLAB] Original: {original_transcript}")
                print(f"[COLAB] Translated: {translated_text}")
                print(f"[COLAB] Language: {detected_language}")
                
                return Response({
                    "transcript": translated_text,  # Return the translated English text
                    "original_transcript": original_transcript,  # Keep original for reference
                    "detected_language": detected_language,
                    "translation_applied": translation_applied,
                    "engine": data.get('engine', 'colab-whisper-ollama')
                })
            else:
                return Response({
                    "error": f"Colab API error: {resp.text}"
                }, status=resp.status_code)
                
        except requests.exceptions.Timeout:
            return Response({
                "error": "Colab request timed out. Please try again."
            }, status=504)
        except requests.exceptions.ConnectionError:
            return Response({
                "error": "Could not connect to Colab. Make sure your Colab notebook is running and ngrok URL is updated."
            }, status=503)
        except Exception as e:
            print(f"[ERROR] Transcription failed: {e}")
            return Response({
                "error": f"Transcription failed: {str(e)}"
            }, status=500)


class TranslateTextView(APIView):
    """
    Standalone translation endpoint using Colab Ollama
    For translating text directly (without audio)
    """
    permission_classes = [AllowAny]

    def post(self, request):
        text = request.data.get('text', '').strip()
        
        if not text:
            return Response({"error": "No text provided."}, status=400)
        
        try:
            # Send text to Colab's Ollama translation endpoint
            resp = requests.post(
                f"{COLAB_API_URL}/api/translate",
                json={"text": text},
                timeout=30
            )
            
            if resp.status_code == 200:
                data = resp.json()
                return Response({
                    "translated": data.get('translated', text),
                    "original": data.get('original', text)
                })
            else:
                return Response({
                    "error": f"Translation failed: {resp.text}"
                }, status=resp.status_code)
                
        except requests.exceptions.Timeout:
            return Response({
                "error": "Translation request timed out."
            }, status=504)
        except requests.exceptions.ConnectionError:
            return Response({
                "error": "Could not connect to Colab translation service."
            }, status=503)
        except Exception as e:
            print(f"[ERROR] Translation failed: {e}")
            return Response({
                "error": f"Translation failed: {str(e)}"
            }, status=500)


# ============== Chat Session Management APIs ==============

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def chat_sessions(request):
    """
    GET: List user's chat sessions (latest 3 only)
    POST: Create a new chat session (auto-deletes oldest if user has 3+ sessions)
    """
    if request.method == 'GET':
        # Get user's 3 most recent sessions only
        sessions = ChatSession.objects.filter(user=request.user, is_active=True)[:3]
        data = []
        for session in sessions:
            data.append({
                'id': session.id,
                'crop': session.crop,
                'title': session.title or session.get_preview(),
                'message_count': session.messages.count(),
                'created_at': session.created_at.isoformat(),
                'updated_at': session.updated_at.isoformat(),
                'preview': session.get_preview(),
            })
        return Response(data)
    
    elif request.method == 'POST':
        # Create new session
        crop = request.data.get('crop', '').lower()
        title = request.data.get('title', '')
        
        if not crop:
            return Response({'error': 'Crop is required'}, status=400)
        
        # Check if user already has 3 or more sessions
        existing_sessions = ChatSession.objects.filter(
            user=request.user, 
            is_active=True
        ).order_by('-updated_at')
        
        # If user has 3 sessions, delete the oldest one
        if existing_sessions.count() >= 3:
            oldest_session = existing_sessions.last()
            oldest_session.delete()  # Permanently delete (or set is_active=False to keep in DB)
            print(f"Deleted oldest session (ID: {oldest_session.id}) to maintain 3-session limit")
        
        # Create new session
        session = ChatSession.objects.create(
            user=request.user,
            crop=crop,
            title=title
        )
        
        return Response({
            'id': session.id,
            'crop': session.crop,
            'title': session.title,
            'created_at': session.created_at.isoformat(),
        }, status=201)


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def chat_session_detail(request, session_id):
    """
    GET: Get all messages in a session
    DELETE: Delete a session
    """
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    
    if request.method == 'GET':
        messages = session.messages.all()
        data = {
            'id': session.id,
            'crop': session.crop,
            'title': session.title or session.get_preview(),
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'messages': [
                {
                    'id': msg.id,
                    'text': msg.text,
                    'is_user': msg.is_user,
                    'metadata': msg.metadata,
                    'created_at': msg.created_at.isoformat(),
                }
                for msg in messages
            ]
        }
        return Response(data)
    
    elif request.method == 'DELETE':
        session.is_active = False
        session.save()
        return Response({'message': 'Session deleted'}, status=204)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_message_to_session(request, session_id):
    """Add a message to an existing chat session"""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    
    text = request.data.get('text', '')
    is_user = request.data.get('is_user', True)
    metadata = request.data.get('metadata', None)
    
    if not text:
        return Response({'error': 'Message text is required'}, status=400)
    
    message = ChatMessage.objects.create(
        session=session,
        text=text,
        is_user=is_user,
        metadata=metadata
    )
    
    # Update session timestamp
    session.save()  # This updates 'updated_at' automatically
    
    return Response({
        'id': message.id,
        'text': message.text,
        'is_user': message.is_user,
        'metadata': message.metadata,
        'created_at': message.created_at.isoformat(),
    }, status=201)
