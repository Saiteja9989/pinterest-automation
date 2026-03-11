"""
fix_missing_images.py — Re-generate Freepik images for pins that have no image_url
Downloads to images/ folder and updates queue with permanent GitHub raw URL.

Usage: python fix_missing_images.py
"""
import json
import os
from freepik_gen import generate_image

QUEUE_FILE = 'pins_queue.json'
GITHUB_RAW = 'https://raw.githubusercontent.com/Saiteja9989/pinterest-automation/main'

with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
    queue = json.load(f)

pins = queue["pins"]
fixed = 0

for i, pin in enumerate(pins):
    if pin.get("image_url") or not pin.get("freepik_prompt"):
        continue

    blog_num = pin.get("blog_number", "x")
    pin_num  = pin.get("pin_number", i + 1)
    filename = f"blog{blog_num}_pin{pin_num}.jpg"

    print(f"\nFixing pin {pin_num} from Blog #{blog_num}: {pin['title'][:50]}...")
    local_path = generate_image(pin["freepik_prompt"], save_filename=filename)

    if local_path:
        # Convert local path to permanent GitHub raw URL
        github_url = f"{GITHUB_RAW}/images/{filename}"
        pins[i]["image_url"] = github_url
        fixed += 1
        with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)
        print(f"  Saved: {github_url}")
    else:
        print(f"  Failed again — try running script again later.")

print(f"\nDone! Fixed {fixed} image(s).")

if fixed:
    print("\nNow push to GitHub:")
    print("  git add images/ pins_queue.json")
    print(f'  git commit -m "Fix missing images"')
    print("  git push")
