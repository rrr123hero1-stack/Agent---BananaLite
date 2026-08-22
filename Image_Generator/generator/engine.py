def format_universal_prompt(prompt: str) -> tuple[str, str]:
    """Structures multi-subject prompts to prevent concept bleeding and hybrid artifacts."""
    
    # 1. Add camera framing & subject placement defaults
    enhanced = (
        f"wide shot cinematic photo of {prompt}, clear distinct separation between subjects, "
        f"action shot, sharp focus, natural lighting, highly detailed, photorealistic, 8k resolution"
    )
    
    # 2. Universal negative prompt to destroy hybrids, cat/dog ears on humans, and soft eyes
    negative = (
        "chimera, hybrid animal human, cat ears, dog ears, furry, animal features on human, "
        "blurry eyes, milky eyes, distorted faces, duplicate people, merged bodies, bad anatomy, "
        "low quality, painting, illustration, drawing, oversaturated, soft focus"
    )
    
    return enhanced, negative