import gc
import os
import re
import time
from typing import Any
from PIL import Image
import torch
from diffusers import AutoPipelineForText2Image, LCMScheduler
from duckduckgo_search import DDGS

from generator.enhancer import ImageQualityEnhancer
from generator.text_weapon import LegalDocumentWeapon


class FastONNXEngine:
    """Adaptive CPU Generator with automatic web search fallback for unknown entities."""

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

        print("\n[Engine] Loading CPU-Accelerated LCM SD 1.5...")
        model_id = "SimianLuo/LCM_Dreamshaper_v7"

        torch.set_num_threads(os.cpu_count() or 8)

        self.pipe = AutoPipelineForText2Image.from_pretrained(
            model_id,
            torch_dtype=torch.float32,
            safety_checker=None,
            low_cpu_mem_usage=True,
        )

        self.pipe.scheduler = LCMScheduler.from_config(self.pipe.scheduler.config)
        self.pipe.enable_attention_slicing()

    def _fetch_web_context_if_needed(self, prompt: str) -> str:
        """Searches DuckDuckGo only if proper nouns/named entities are detected."""
        # Simple heuristic: check if prompt contains capitalized proper nouns or specific celebrity words
        words = prompt.split()
        has_proper_nouns = any(w[0].isupper() for w in words[1:] if len(w) > 1)
        
        if not has_proper_nouns:
            return prompt

        print(f"[Engine] Searching web context for unknown entity in: '{prompt}'...")
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(f"visual description of {prompt}", max_results=1))
                if results and "body" in results[0]:
                    snippet = results[0]["body"][:150]
                    # Clean snippet text
                    snippet = re.sub(r"[^\w\s,]", "", snippet)
                    enhanced = f"{prompt}, visual appearance: {snippet}"
                    print(f"[Engine] Web context added: {snippet[:60]}...")
                    return enhanced
        except Exception as e:
            print(f"[Engine] Web lookup skipped: {e}")

        return prompt

    def generate(
        self,
        prompt: str,
        steps: int = 4,
        ratio: str = "16:9",
        long_text_overlay: str | None = None,
    ) -> Any:
        self._load_model()

        # Step 1: Conditionally fetch web context for named people/entities
        active_prompt = self._fetch_web_context_if_needed(prompt)

        width, height = self.RATIOS.get(ratio, (768, 432))
        print(f"\n[Engine] Rendering {width}x{height} | Steps: {steps}")

        start_time = time.time()

        person_keywords = [
            "boy", "girl", "man", "woman", "person", 
            "child", "human", "guy", "lady", "developer", "beast"
        ]
        is_person = any(k in prompt.lower() for k in person_keywords) or any(w[0].isupper() for w in prompt.split())

        if is_person:
            enhanced_prompt = (
                f"{active_prompt}, wearing suitable attire, "
                f"detailed facial features, clear eyes, crisp focus, photorealistic"
            )
            negative_prompt = (
                "nude, unclothed, bare chest, shirtless, blurred face, blurry features, "
                "bad eyes, distorted face, extra limbs, bad anatomy, bad hands, low quality"
            )
        else:
            enhanced_prompt = f"{active_prompt}, high resolution, crisp details, photorealistic, 8k"
            negative_prompt = "low quality, blurry, distorted, noisy, oversaturated, bad composition"

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