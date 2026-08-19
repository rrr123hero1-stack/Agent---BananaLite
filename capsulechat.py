from flask import Flask, request, jsonify
from flask_cors import CORS
import ollama
from flask import Flask, request, jsonify
from flask_cors import CORS
import ollama

app = Flask(__name__)
CORS(app)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    print(f"\n[TERMINAL] Received Question: {data['prompt']}") # This shows in your terminal
    
    response = ollama.chat(
        model='qwen3-vl:4b',
        messages=[{'role': 'user', 'content': data['prompt']}]
    )
    
    answer = response['message']['content']
    print(f"[TERMINAL] Returning Answer: {answer[:50]}...") # Proof of life
    return jsonify({'response': answer})

if __name__ == '__main__':
    print("--- CapsuleChat Bridge Active on http://127.0.0.1:5000 ---")
    app.run(port=5000)