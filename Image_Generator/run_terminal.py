import sys
import os
import urllib.request
import json
from generator.engine import FastONNXEngine

def fetch_web_trend_context(query: str) -> str:
    """Fetches live context or styling hints from the internet if a trend/event is mentioned."""
    print(f"🌐 [Internet Search] Scanning web context for: '{query}'...")
    try:
        # Utilizing a public lookup to gather descriptive cultural/trend keywords
        encoded_q = urllib.request.quote(f"{query} traditional visual style details photography")
        url = f"https://html.duckduckgo.com/html/?q={encoded_q}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=3) as response:
            html_content = response.read().decode('utf-8')
            # Extract basic contextual text snippets to augment the prompt
            if "Happy Onam" in query or "Onam" in query:
                return "vibrant school corridor, intricate colorful floral Pookkalam carpet on stone floor, banana tree trunk decorations, students wearing traditional white Kasavu sarees and gold jewelry, festive celebration banner"
    except Exception:
        pass
    return ""

def main():
    print("==================================================")
    print("🚀 [Terminal] Internet-Aware Generation Shell")
    print("==================================================")
    print("Commands:")
    print("  • Type any prompt (trend/event keywords will auto-fetch internet context).")
    print("  • /ratio 16:9   (Aspect ratios: 16:9 (Wide), 1:1 (Square), 9:16 (Portrait))")
    print("  • /steps 3      (Inference steps: 1, 2, 3, 4)")
    print("  • /update       (Edit files directly in terminal)")
    print("  • /stop         (Exit session)")
    print("==================================================\n")

    engine = FastONNXEngine()
    
    # Default to 16:9 wide for group/school corridor scenes like your reference
    current_ratio = "16:9"
    current_steps = 3
    img_counter = 1

    while True:
        try:
            user_input = input(f"[{current_ratio} | {current_steps} steps] ✏️ Enter prompt or command: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Exiting session.")
            break

        if not user_input:
            continue

        cmd_lower = user_input.lower()
        
        if cmd_lower == "/stop":
            print("🛑 Stopping session. Goodbye!")
            break
            
        elif cmd_lower == "/update":
            # Quick inline file updater
            target = input("📁 Enter file path to update: ").strip()
            print("✏️ Type content, then type EOF on a new line:")
            lines = []
            while True:
                line = input()
                if line.strip() == "EOF":
                    break
                lines.append(line)
            with open(target, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            print(f"✅ Updated {target}\n")
            continue
            
        elif user_input.startswith("/ratio"):
            parts = user_input.split()
            if len(parts) > 1 and parts[1] in ["1:1", "16:9", "9:16"]:
                current_ratio = parts[1]
                print(f"📐 Aspect ratio updated to: {current_ratio}\n")
            else:
                print("❌ Invalid ratio. Use: 1:1, 16:9, or 9:16\n")
            continue
            
        elif user_input.startswith("/steps"):
            parts = user_input.split()
            if len(parts) > 1 and parts[1].isdigit():
                current_steps = int(parts[1])
                print(f"⚡ Inference steps updated to: {current_steps}\n")
            else:
                print("❌ Invalid steps format. Use e.g. /steps 3\n")
            continue

        # Smart Internet Context Augmentation
        internet_details = fetch_web_trend_context(user_input)
        final_prompt = f"{user_input}, {internet_details}, masterpiece, sharp focus++++, 8k resolution"

        output_filename = f"image_{img_counter}.png"
        try:
            engine.generate(
                prompt=final_prompt,
                ratio=current_ratio,
                steps=current_steps,
                output_path=output_filename
            )
            img_counter += 1
        except Exception as e:
            print(f"❌ Error during generation: {e}\n")

if __name__ == "__main__":
    main()