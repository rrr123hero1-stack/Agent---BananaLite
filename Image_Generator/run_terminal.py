import os
import time
from generator.engine import FastONNXEngine


def main() -> None:
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("  MAX-CLEAN 4-SIZE BATCH GENERATOR (SD 1.5 CPU)")
    print("  Type '/stop' to exit.")
    print("=" * 60)

    engine = FastONNXEngine()

    while True:
        try:
            prompt = input("\nEnter Prompt (or '/stop' to exit): ").strip()

            if not prompt:
                continue

            if prompt.lower() == "/stop":
                print("\n[System] Exiting. Goodbye!")
                break

            mode = input("Generate all 4 sizes? [y/N]: ").strip().lower()
            overlay_text = input("Text Overlay (Press Enter to skip): ").strip()
            long_text = overlay_text if len(overlay_text) > 2 else None

            # All 4 supported aspect ratios
            ratios_to_gen = ["16:9", "1:1", "9:16", "4:3"] if mode == "y" else ["16:9"]

            print(f"\n[System] Starting render queue ({len(ratios_to_gen)} tasks)...")
            batch_start = time.time()

            for idx, ratio in enumerate(ratios_to_gen, 1):
                print(f"\n--- Processing {idx}/{len(ratios_to_gen)}: Aspect Ratio {ratio} ---")
                
                img = engine.generate(
                    prompt=prompt,
                    steps=4,
                    ratio=ratio,
                    long_text_overlay=long_text,
                )

                timestamp = int(time.time())
                filename = f"gen_{timestamp}_{ratio.replace(':', 'x')}.png"
                filepath = os.path.join(output_dir, filename)

                img.save(filepath)
                print(f"✨ Saved: {filepath}")

            total_elapsed = time.time() - batch_start
            print(f"\n[Batch Complete] Processed {len(ratios_to_gen)} images in {total_elapsed:.2f}s")

        except KeyboardInterrupt:
            print("\n\n[System] Interrupted by user. Exiting...")
            break
        except Exception as e:
            print(f"\n❌ Error during generation: {e}")


if __name__ == "__main__":
    main()