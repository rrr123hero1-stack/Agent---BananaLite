import os
import sys

os.environ["HF_HOME"] = "/tmp/huggingface_cache"
os.environ["TRANSFORMERS_CACHE"] = "/tmp/huggingface_cache"

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from generator.engine import FastONNXEngine

def main() -> None:
    print("=" * 60)
    print("  ONNX FAST GENERATOR (15 STEPS / ~40 SEC)            ")
    print("  Type '/stop' to exit.                               ")
    print("=" * 60)

    engine = FastONNXEngine()
    gen_count = 0

    while True:
        prompt = input("\nEnter Prompt (or '/stop' to exit): ").strip()
        if prompt.lower() == "/stop":
            break

        if not prompt:
            prompt = "a boy eating barbecue in a restaurant"

        output_image = engine.generate(
            prompt=prompt,
            steps=6,
            ratio="4:4",

        )

        gen_count += 1
        out_path = os.path.join(os.path.dirname(__file__), f"output_{gen_count}.png")
        output_image.save(out_path)
        print(f"\nSUCCESS! Saved to: {os.path.abspath(out_path)}")

if __name__ == "__main__":
    main()