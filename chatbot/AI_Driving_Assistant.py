import os
import json
import faiss
import numpy as np
import hashlib
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
from threading import Thread
from queue import Queue
import time

load_dotenv("key.env")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is missing.")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

CAR_SAFETY_KB = {
    "drowsiness_prevention": "Take regular breaks every 2 hours, stay hydrated, avoid heavy meals, and maintain good posture while driving.",
    "fatigue_signs": "Common signs include frequent yawning, heavy eyelids, drifting between lanes, and difficulty focusing.",
    "defensive_driving": "Maintain safe following distance, scan the road ahead, anticipate other drivers' actions, and avoid distractions.",
    "weather_conditions": "Adjust speed for rain, snow, or fog. Increase following distance and use headlights appropriately.",
    "emergency_handling": "Stay calm, maintain control, and follow proper procedures for skids, brake failure, or tire blowouts.",
    "vehicle_maintenance": "Regularly check tire pressure, brakes, lights, and fluid levels. Keep windshield clean and wipers in good condition.",
    "night_driving": "Use high beams appropriately, reduce speed, and be extra cautious of pedestrians and animals.",
    "distraction_prevention": "Put phone away, set GPS before driving, and avoid eating or adjusting controls while moving.",
    "crash_prevention": "Maintain proper speed, use turn signals, check blind spots, and be aware of traffic patterns.",
    "first_aid_kit": "Keep emergency supplies including bandages, antiseptic, flashlight, and emergency contact information in your vehicle."
}

def get_embedding(text: str) -> np.array:
    hash_val = hashlib.md5(text.encode()).digest()
    vector = np.frombuffer(hash_val, dtype=np.uint8).astype(np.float32)
    norm = np.linalg.norm(vector)
    return vector / norm if norm != 0 else vector

embedding_dim = 16
kb_texts = list(CAR_SAFETY_KB.values())
kb_embeddings = np.stack([get_embedding(text) for text in kb_texts])
kb_index = faiss.IndexFlatL2(embedding_dim)
kb_index.add(kb_embeddings)

def retrieve_relevant_context(query: str, top_k=2):
    query_embedding = get_embedding(query)
    query_embedding = np.expand_dims(query_embedding, axis=0)
    distances, indices = kb_index.search(query_embedding, top_k)
    matched_texts = [kb_texts[idx] for idx in indices[0]]
    return "\n".join(matched_texts)

def generate_response(query: str) -> str:
    context = retrieve_relevant_context(query)
    prompt = f"""As a car safety expert, use this knowledge to answer the question:

Context:
{context}

User question: {query}

Provide a clear and structured response:
- List specific signs and prevention methods.
- Include practical tips and best practices.
- Mention emergency procedures if relevant.
- Use numbered steps for instructions.
- Explain relevant safety techniques and precautions.
- Always emphasize the importance of staying alert and following traffic rules."""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating response: {str(e)}"

# Queue to handle asynchronous response generation
response_queue = Queue()

def process_request(query: str):
    """Background thread to generate response and put it in the queue."""
    response = generate_response(query)
    response_queue.put(response)

# Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all domains

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    query = data.get("query", "")
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    # Start a new thread to process the request
    thread = Thread(target=process_request, args=(query,))
    thread.start()
    
    # Wait for the response with a reasonable timeout (e.g., 30 seconds)
    # Adjust this timeout based on your needs
    try:
        response = response_queue.get(timeout=3000)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": f"Request timed out or failed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)