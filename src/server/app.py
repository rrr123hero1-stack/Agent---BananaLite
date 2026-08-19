from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import ollama
import os

# Point to your React 'dist' folder
app = Flask(__name__, static_folder='dist')
CORS(app)

# Serve the React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# Your API Endpoint
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    response = ollama.chat(
        model='qwen3-vl:4b',
        messages=[{'role': 'user', 'content': data['prompt']}]
    )
    return jsonify({'response': response['message']['content']})

if __name__ == '__main__':
    app.run(port=5000)