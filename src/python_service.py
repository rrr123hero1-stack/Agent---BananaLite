import torch
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from diffusers import AutoPipelineForText2Image, EulerAncestralDiscreteScheduler
import io
import time

app = FastAPI(title="Custom Fast Image Generation Engine")

# Base Model (SDXL-Turbo is ideal for fast 1-4 step generations)
MODEL_ID = "stabilityai/sdxl-turbo"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32

pipe = None

class ImageRequest(BaseModel):
    prompt: str
    target_time: float = 10.0   # <10s, <20s, or <30s target budget
    aspect_ratio: str = "16:9"  # "4:4", "16:9", "9:16", "1:1", "Auto"

@app.on_event("startup")
async def load_image_model():
    """Load model once into VRAM with memory optimizations."""
    global pipe
    print(f"Loading Image Model ({MODEL_ID}) on {DEVICE}...")
    start_time = time.time()
    try:
        pipe = AutoPipelineForText2Image.from_pretrained(
            MODEL_ID, 
            torch_dtype=DTYPE, 
            variant="fp16" if DEVICE == "cuda" else None
        )
        pipe.to(DEVICE)
        
        # Optimize memory usage
        if DEVICE == "cuda":
            pipe.enable_model_cpu_offload()

        pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)
        print(f"Image Engine ready in {time.time() - start_time:.2f}s!")
    except Exception as e:
        print(f"Error loading image model: {e}")

def calculate_dimensions(aspect_ratio: str, max_height: int) -> tuple[int, int]:
    """
    Computes (Width, Height) snapped to multiples of 8 (required for VAE).
    """
    if aspect_ratio == "Auto":
        aspect_ratio = "16:9" # Default fallback for Auto aspect ratio

    if aspect_ratio in ["1:1", "4:4"]:
        return max_height, max_height
    elif aspect_ratio == "16:9":
        # Landscape
        height = max_height
        width = int(height * (16 / 9))
    elif aspect_ratio == "9:16":
        # Portrait (Stories / Shorts)
        width = max_height
        height = int(width * (16 / 9))
    else:
        width, height = max_height, max_height

    # Snap to nearest multiple of 8
    width = (width // 8) * 8
    height = (height // 8) * 8
    return width, height

@app.post("/generate-image")
async def generate_image(request: ImageRequest):
    if pipe is None:
        raise HTTPException(status_code=503, detail="Image engine not loaded.")

    start_time = time.time()

    # 1. Map Time Budget to Resolution & Inference Steps
    if request.target_time <= 10.0:
        # <10s Target: Basic Quality (~480p, 1 Step)
        max_h = 480
        inference_steps = 1
    elif request.target_time <= 20.0:
        # <20s Target: Normal Quality (~540p-720p, 2 Steps)
        max_h = 576
        inference_steps = 2
    else:
        # <30s Target: High Quality (~720p-1080p, 4 Steps)
        max_h = 720
        inference_steps = 4

    # 2. Compute Dimensions according to aspect ratio
    width, height = calculate_dimensions(request.aspect_ratio, max_h)

    print(f"Generating Image | Budget: <{request.target_time}s | Res: {width}x{height} | Steps: {inference_steps}")

    try:
        # 3. Fast Inference Generation
        output = pipe(
            prompt=request.prompt,
            width=width,
            height=height,
            num_inference_steps=inference_steps,
            guidance_scale=0.0, # 0.0 required for SDXL Turbo
            output_type="pil"
        ).images[0]

        # 4. Convert PIL to Binary Byte Stream
        img_byte_arr = io.BytesIO()
        output.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()

        elapsed = time.time() - start_time
        print(f"Image generated in {elapsed:.2f} seconds!")

        return Response(content=img_bytes, media_type="image/png")

    except Exception as e:
        print(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)