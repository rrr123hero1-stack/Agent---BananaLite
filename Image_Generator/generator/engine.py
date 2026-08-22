import gc
import os
import time
from typing import Any
from PIL import Image
from optimum.onnxruntime import ORTStableDiffusionPipeline

from generator.enhancer import ImageQualityEnhancer
from generator.text_weapon import LegalDocumentWeapon


class FastONNXEngine:
    """CPU ONNX Accelerated Engine for 15-step sharp generations (~40s)."""

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

        print("\n[ONNX Engine] Loading ONNX SD 1.5 Pipeline...")
        model_id = "runwayml/stable-diffusion-v1-5"

        # Export and run via CPU ONNX Execution Provider
        self.pipe = ORTStableDiffusionPipeline.from_pretrained(
            model_id,
            export=True,
            provider="CPUExecutionProvider",
        )

    def generate(
        self,
        prompt: str,
        steps: int = 15,
        ratio: str = "1:1",
        long_text_overlay: str | None = None,
    ) -> Any:
        self._load_model()

        width, height = self.RATIOS.get(ratio, (512, 512))
        print(f"\n[ONNX Engine] Rendering {width}x{height} | Steps: {steps}")

        start_time = time.time()

        enhanced_prompt = (
            f"{prompt}, dressed in casual clothing, t-shirt, "
            f"highly detailed face, sharp clear eyes, crisp focus, photorealistic"
        )
        negative_prompt = (
            "nude, unclothed, bare chest, shirtless, blurred face, blurry features, "
            "bad eyes, distorted face, extra limbs, bad anatomy, low quality"
        )

        output = self.pipe(
            prompt=enhanced_prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=steps,
            guidance_scale=7.5,
            width=width,
            height=height,
        )
        img = output.images[0]

        if long_text_overlay and len(long_text_overlay) > 10:
            img = self.text_weapon.apply_overlay(img, long_text_overlay)

        img = self.enhancer.process(img, level=2)

        elapsed = time.time() - start_time
        print(f"[ONNX Engine] Generation finished in {elapsed:.2f}s")

        gc.collect()
        return img