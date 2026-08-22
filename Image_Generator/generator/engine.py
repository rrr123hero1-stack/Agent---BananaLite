import gc
import os
import re
import time
from typing import Any
from PIL import Image
import torch
from diffusers import AutoPipelineForText2Image, LCMScheduler, AutoencoderTiny
from duckduckgo_search import DDGS

from generator.enhancer import ImageQualityEnhancer
from generator.text_weapon import LegalDocumentWeapon


class FastONNXEngine:
    """Optimized CPU Engine with FreeU V2, TinyVAE decoding, and DuckDuckGo fallback."""

    def __init__(self) -> None:
        os.environ["HF_HOME"] = "/tmp/huggingface_cache"
        os.environ["TRANSFORMERS_CACHE"] = "/tmp/huggingface_cache"

        self.text_weapon = LegalDocumentWeapon()
        self.enhancer = ImageQualityEnhancer()
        self.pipe = None
        self.RATIOS: dict[str, tuple[int, int]] = {
            "1:1": (512, 512),
            "16:9": (768, 432),
            "9:16": (432, 768),
        }

    def _load_model(self) -> None:
        if self.pipe is not None:
            return

        print("\n[Engine] Loading CPU LCM SD 1.5 + FreeU + TinyVAE...")
        model_id = "SimianLuo/LCM_Dreamshaper_v7"

        torch.set_num_threads(os.cpu_count() or 8)

        self.pipe = AutoPipelineForText2Image.from_pretrained(
            model_id,
            torch_dtype=torch.float32,
            safety_checker=None,
            low_cpu_mem_usage=True,
        )

        self.pipe.scheduler = LCMScheduler.from_config(self.pipe.scheduler.config)

        # 1. Ultra-fast and sharp TinyVAE decoder
        self.pipe.vae = AutoencoderTiny.from_pretrained(
            "madebyollin/taesd", 
            torch_dtype=torch.float32
        )

        # 2. FreeU V2 (sharpens eyes, paws, and organic textures)
        self.pipe.enable_freeu(s1=0.9, s2=0.2, b1=1.2, b2=1.4)
        
        self.pipe.enable_attention_slicing()

    def _fetch_web_context_if_needed(self, prompt: str) -> str:
        words = prompt.split()
        has_proper_nouns = any(w[0].isupper() for w in words[1:] if len(w) > 1)
        
        if not has_proper_nouns:
            return prompt

        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(f"visual description of {prompt}", max_results=1))
                if results and "body" in results[0]:
                    snippet = results[0]["body"][:150]
                    snippet = re.sub(r"[^\w\s,]", "", snippet)
                    return f"{prompt}, visual appearance: {snippet}"
        except Exception:
            pass

        return prompt

    def _build_bulletproof_prompts(self, prompt: str) -> tuple[str, str]:
        enhanced_prompt = (
            f"{prompt}, highly detailed, sharp focus, crisp edges, clear distinct separation between subjects, "
            f"photorealistic, 8k resolution, cinematic lighting"
        )
        negative_prompt = (
            "chimera, hybrid animal human, cat ears, dog ears, furry, animal features on human, "
            "motion blur, speed blur, ghosting, blurry, out of focus, duplicate subjects, merged bodies, "
            "fused limbs, distorted hands, fingers merged with face, distorted mouth, milky eyes, bad eyes, "
            "bad anatomy, extra animals, low quality, soft focus, painting, illustration, render artifacts"
        )
        return enhanced_prompt, negative_prompt

    def generate(
        self,
        prompt: str,
        steps: int = 4,
        ratio: str = "16:9",
        long_text_overlay: str | None = None,
    ) -> Any:
        self._load_model()

        active_prompt = self._fetch_web_context_if_needed(prompt)
        enhanced_prompt, negative_prompt = self._build_bulletproof_prompts(active_prompt)

        width, height = self.RATIOS.get(ratio, (768, 432))
        print(f"\n[Engine] Rendering {width}x{height} | Steps: {steps}")

        start_time = time.time()

        output = self.pipe(
            prompt=enhanced_prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=steps,
            guidance_scale=8.0,
            width=width,
            height=height,
        )
        img = output.images[0]

        if long_text_overlay and len(long_text_overlay) > 10:
            img = self.text_weapon.apply_overlay(img, long_text_overlay)

        img = self.enhancer.process(img, level=2)

        elapsed = time.time() - start_time
        print(f"[Engine] Generation finished in {elapsed:.2f}s")

        gc.collect()
        return img