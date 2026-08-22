import gc
import os
import time
from typing import Any
from PIL import Image
import torch
from diffusers import AutoPipelineForText2Image, LCMScheduler

from generator.enhancer import ImageQualityEnhancer
from generator.fast_corrector import FastCPUCorrector
from generator.text_weapon import LegalDocumentWeapon


class FastONNXEngine:
    """Adaptive CPU Generator supporting both human and general scene prompts."""

    def __init__(self) -> None:
        os.environ["HF_HOME"] = "/tmp/huggingface_cache"
        os.environ["TRANSFORMERS_CACHE"] = "/tmp/huggingface_cache"

        self.text_weapon = LegalDocumentWeapon()
        self.enhancer = ImageQualityEnhancer()
        self.corrector = FastCPUCorrector()
        self.pipe = None
        self.RATIOS: dict[str, tuple[int, int]] = {
            "1:1": (512, 512),
            "16:9": (768, 432),
            "9:16": (432, 768),
        }

    def _load_model(self) -> None:
        if self.pipe is not None:
            return

        print("\n[Engine] Loading CPU-Accelerated LCM SD 1.5 into /tmp...")
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

    def generate(
        self,
        prompt: str,
        steps: int = 4,
        ratio: str = "1:1",
        long_text_overlay: str | None = None,
    ) -> Any:
        self._load_model()

        width, height = self.RATIOS.get(ratio, (512, 512))
        print(f"\n[Engine] Rendering {width}x{height} | Steps: {steps}")

        start_time = time.time()

        person_keywords = [
            "boy", "girl", "man", "woman", "person", 
            "child", "human", "guy", "lady", "developer"
        ]
        is_person = any(k in prompt.lower() for k in person_keywords)

        if is_person:
            enhanced_prompt = (
                f"{prompt}, wearing suitable attire according to situation, "
                f"detailed facial features, clear eyes, crisp focus, photorealistic"
            )
            negative_prompt = (
                "nude, unclothed, bare chest, shirtless, blurred face, blurry features, "
                "bad eyes, distorted face, extra limbs, bad prompt adherence, bad anatomy, low quality"
            )
        else:
            enhanced_prompt = f"{prompt}, high resolution, crisp details, photorealistic, 8k"
            negative_prompt = "low quality, blurry, distorted, noisy, oversaturated, bad composition"

        output = self.pipe(
            prompt=enhanced_prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=steps,
            guidance_scale=8.6,
            width=width,
            height=height,
        )
        img = output.images[0]

        if long_text_overlay and len(long_text_overlay) > 10:
            img = self.text_weapon.apply_overlay(img, long_text_overlay)

        img = self.enhancer.process(img, level=2)

        # Run fast corrector
        self.corrector.pipe = self.pipe
        img = self.corrector.correct(img, prompt)

        elapsed = time.time() - start_time
        print(f"[Engine] Total process finished in {elapsed:.2f}s")

        gc.collect()
        return img