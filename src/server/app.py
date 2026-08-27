import os
import base64
from io import BytesIO
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import torch
from diffusers import StableDiffusionPipeline, DDIMScheduler

# Locate root build directory relative to src/server/app.py
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
DIST_DIR = os.path.join(BASE_DIR, "dist")

app = Flask(__name__, static_folder=DIST_DIR, static_url_path="")

# Enable CORS for React Vite development server (Port 5173 / 3000 / Codespaces)
CORS(app, resources={r"/*": {"origins": "*"}})

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[*] Loading DreamShaper v8 engine onto {device}...")

# 1. Load DreamShaper v8 Base Model
base_model_id = "Lykon/dreamshaper-8"
pipe = StableDiffusionPipeline.from_pretrained(
    base_model_id,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    safety_checker=None,
    use_safetensors=True
)

# 2. Load Hyper-SD 4-Step LoRA Weights
pipe.load_lora_weights("ByteDance/Hyper-SD", weight_name="Hyper-SD15-4steps-lora.safetensors")
pipe.fuse_lora()

# 3. Configure DDIM Scheduler for 4-Step Hyper-SD
pipe.scheduler = DDIMScheduler.from_config(
    pipe.scheduler.config, 
    timestep_spacing="trailing"
)
pipe.to(device)

DEFAULT_PROMPT = "An intricate ornate mechanical clockwork mechanism, high detail, micro texture, 8k"

def run_inference(prompt, width=512, height=512, steps=4):
    """Generates image using DreamShaper v8 + Hyper-SD."""
    image = pipe(
        prompt=prompt,
        width=width,
        height=height,
        num_inference_steps=steps,
        guidance_scale=0.0
    ).images[0]
    
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# Health Check Route targeted by App.jsx on component mount
@app.route('/api/health', methods=['GET'])
def health_check():
    """Returns connection confirmation message to App.jsx."""
    return jsonify({
        "status": "online",
        "message": "Connected to Agent Banana Lite Backend Engine!",
        "device": device,
        "target": "src/App.jsx"
    }), 200

# Main Generation Route targeted by form submission in App.jsx
@app.route('/generate', methods=['POST'])
def generate():
    """POST endpoint handling image generation requests from App.jsx."""
    try:
        data = request.get_json() or {}
        prompt = data.get('prompt', DEFAULT_PROMPT)
        ratio = data.get('ratio', '1:1')
        steps = int(data.get('steps', 4))

        dim_map = {
            '1:1': (512, 512),
            '16:9': (832, 464),
            '9:16': (464, 832)
        }
        width, height = dim_map.get(ratio, (512, 512))

        img_str = run_inference(prompt, width, height, steps)

        return jsonify({
            "status": "success",
            "image_url": f"data:image/jpeg;base64,{img_str}"
        }), 200

    except Exception as e:
        print(f"[-] Generation Error: {e}")
        return jsonify({"error": str(e)}), 500

# Serve compiled Vite app index if accessed via root URL
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join(DIST_DIR, path)):
        return send_from_directory(DIST_DIR, path)
    elif os.path.exists(os.path.join(DIST_DIR, "index.html")):
        return send_from_directory(DIST_DIR, "index.html")
    else:
        return jsonify({
            "status": "active",
            "info": "Backend running. Start Vite dev server for src/App.jsx on Port 5173."
        }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)