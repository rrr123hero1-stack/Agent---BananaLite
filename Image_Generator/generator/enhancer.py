from typing import Any

from PIL import ImageEnhance


class ImageQualityEnhancer:
    """Post-processing tool (<5MB) scaling detail enhancement per tier level."""

    def process(self, img: Any, level: int = 2) -> Any:
        if level == 1:
            return img

        if level == 2:
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.20)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.05)
            return img

        # Level 3 Pro Multi-Pass
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.45)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.12)
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.08)
        return img