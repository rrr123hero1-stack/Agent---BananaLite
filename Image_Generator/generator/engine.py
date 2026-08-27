import os
import torch
from diffusers import DiffusionPipeline, DDIMScheduler
from compel import Compel

class FastONNXEngine:
    def __init__(self):
        os.environ["HF_HOME"] = "/tmp/huggingface_cache"
        os.environ["TRANSFORMERS_CACHE"] = "/tmp/huggingface_cache"
        
        self.model_id = "Lykon/dreamshaper-8"
        self.lora_repo = "ByteDance/Hyper-SD"
        self.lora_name = "Hyper-SD15-1step-lora.safetensors"
        
        self.pipe = None
        self.compel = None
        
        self.ratio_map = {
            "1:1": (512, 512),
            "16:9": (768, 448),
            "9:16": (448, 768)
        }

    def _load_model(self):
        if self.pipe is not None:
            return

        print("\n⏳ [Engine] Initializing model into RAM...")
        
        self.pipe = DiffusionPipeline.from_pretrained(
            self.model_id,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
            safety_checker=None
        )
        
        # Load weights without heavy fusing
        self.pipe.load_lora_weights(self.lora_repo, weight_name=self.lora_name)
        self.pipe.scheduler = DDIMScheduler.from_config(self.pipe.scheduler.config, timestep_spacing="trailing")
        
        self.pipe.enable_attention_slicing()
        self.pipe.unet.to(memory_format=torch.channels_last)
        
        self.compel = Compel(tokenizer=self.pipe.tokenizer, text_encoder=self.pipe.text_encoder)
        print("🚀 [Engine] Model ready!\n")

    def generate(self, prompt: str, ratio: str = "16:9", steps: int = 3, output_path: str = "output.png"):
        self._load_model()
        
        width, height = self.ratio_map.get(ratio, (768, 448))
        print(f"🎨 [Engine] Rendering layout {ratio} ({width}x{height}) | Steps: {steps}")
        print(f"📝 Prompt: {prompt}")
        
        conditioning = self.compel(prompt)
        g_scale = 0.0 if steps == 1 else 1.0
        
        image = self.pipe(
            prompt_embeds=conditioning,
            num_inference_steps=steps,
            guidance_scale=g_scale,
            cross_attention_kwargs={"scale": 1.0}, # Applies LoRA dynamically safely
            width=width,
            height=height
        ).images[0]
        
        image.save(output_path)
        print(f"✅ [Engine] Saved artifact to: {output_path}\n")
        return output_path