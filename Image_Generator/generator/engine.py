import gc
import os
import re
import time
from typing import Any
from PIL import Image
import torch

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

from diffusers import AutoPipelineForText2Image
from generator.enhancer import ImageQualityEnhancer
from generator.text_weapon import LegalDocumentWeapon


class FastONNXEngine:
    """SDXL-Turbo CPU Engine: Native HD Resolution & Low Memory Footprint."""

    def __init__(self) -> None:
        os.environ["HF_HOME"] = "/tmp/huggingface_cache"
        os.environ["TRANSFORMERS_CACHE"] = "/tmp/huggingface_cache"

        self.text_weapon = LegalDocumentWeapon()
        self.enhancer = ImageQualityEnhancer()
        self.pipe = None
        
        # Native HD Ratios tuned for SDXL
        self.RATIOS: dict[str, tuple[int, int]] = {
            "16:9": (1024, 576),
            "1:1": (768, 768),
            "9:16": (576, 1024),
            "4:3": (896, 672),
        }

    def _load_model(self) -> None:
        if self.pipe is not None:
            return

        print("\n[Engine] Downloading and loading SDXL-Turbo (Native HD)...")
        model_id = "stabilityai/sdxl-turbo"

        torch.set_num_threads(os.cpu_count() or 8)

        self.pipe = AutoPipelineForText2Image.from_pretrained(
            model_id,
            dtype=torch.float32,
            safety_checker=None,
            low_cpu_mem_usage=True,
        )

        # RAM Optimization (Keeps peak memory under ~4.8 GB)
        self.pipe.enable_attention_slicing()
        self.pipe.enable_vae_slicing()

    def _build_max_detail_prompt(self, prompt: str) -> str:
        return (
            f"{prompt}, ultra-detailed 8k resolution, razor sharp focus, natural skin pores, "
            f"photorealistic lighting, clear legible typography, masterwork"
        )

    def _sharpen_image(self, pil_img: Image.Image) -> Image.Image:
        if not HAS_CV2:
            return pil_img
        img_np = np.array(pil_img)
        gaussian_blur = cv2.GaussianBlur(img_np, (0, 0), 1.5)
        sharpened = cv2.addWeighted(img_np, 1.3, gaussian_blur, -0.3, 0)
        return Image.fromarray(sharpened)

    def generate(
        self,
        prompt: str,
        steps: int = 2,  # SDXL-Turbo peaks at 1-2 steps
        ratio: str = "16:9",
        long_text_overlay: str | None = None,
    ) -> Any:
        self._load_model()

        enhanced_prompt = self._build_max_detail_prompt(prompt)
        width, height = self.RATIOS.get(ratio, (1024, 576))

        print(f"\n[Engine] Rendering {width}x{height} | Steps: {steps}")
        start_time = time.time()

        # Guidance scale set to 1.0 for optimal SDXL-Turbo output
        output = self.pipe(
            prompt=enhanced_prompt,
            num_inference_steps=steps,
            guidance_scale=1.0,
            width=width,
            height=height,
        )
        img = output.images[0]

        img = self._sharpen_image(img)

        if long_text_overlay and len(long_text_overlay) > 2:
            img = self.text_weapon.apply_overlay(img, long_text_overlay)

        img = self.enhancer.process(img, level=2)

        elapsed = time.time() - start_time
        print(f"[Engine] Generation completed in {elapsed:.2f}s")

        gc.collect()
        return img