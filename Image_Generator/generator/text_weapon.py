from typing import Any

from PIL import Image, ImageDraw, ImageFont


class LegalDocumentWeapon:
    """Renders 100% legible 70+ word text overlays with paper texture blending."""

    def apply_overlay(
        self, base_img: Any, text: str, font_size: int = 16
    ) -> Any:
        base = base_img.convert("RGBA")
        txt_layer = Image.new("RGBA", base.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)

        try:
            font = ImageFont.truetype("DejaVuSansMono.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

        margin = 80
        max_width = base.width - (margin * 2)
        words = text.split()
        lines: list[str] = []
        current_line: list[str] = []

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if (bbox[2] - bbox[0]) <= max_width:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))

        y_offset = 100
        for line in lines:
            draw.text(
                (margin, y_offset), line, fill=(28, 32, 38, 240), font=font
            )
            y_offset += font_size + 6

        blended = Image.alpha_composite(base, txt_layer)
        return blended.convert("RGB")