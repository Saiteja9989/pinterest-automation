"""
generate.py — Run locally every Sunday
Reads blog_input.json → generates blog + 10 pins → adds to pins_queue.json

Usage: python generate.py
"""
import json
import os
from groq_gen import generate_blog_html, generate_pin_content
from freepik_gen import generate_10_images
from blogger_up import upload_blog_post

INPUT_FILE = 'blog_input.json'
QUEUE_FILE = 'pins_queue.json'


def load_input():
    with open(INPUT_FILE, 'r') as f:
        return json.load(f)


def load_queue():
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, 'r') as f:
            return json.load(f)
    return {"pins": []}


def save_queue(queue):
    with open(QUEUE_FILE, 'w') as f:
        json.dump(queue, f, indent=2)


def run():
    data = load_input()
    blog_number = data["blog_number"]
    blog_title  = data["blog_title"]
    category    = data["category"]
    products    = data["products"]

    print(f"\n{'='*60}")
    print(f"Blog #{blog_number}: {blog_title}")
    print(f"Category: {category} | Products: {len(products)}")
    print(f"{'='*60}")

    # Step 1: Generate blog HTML
    print("\n[1/4] Generating blog HTML with Groq...")
    html = generate_blog_html(blog_title, category, products)
    print(f"Blog HTML generated ({len(html)} chars)")

    # Step 2: Upload to Blogger
    print("\n[2/4] Uploading to Blogger...")
    blog_url = upload_blog_post(blog_title, html)
    if not blog_url:
        print("ERROR: Blog upload failed!")
        return

    # Step 3: Generate 10 pin titles, descriptions, prompts
    print("\n[3/4] Generating 10 pin contents with Groq...")
    pins = generate_pin_content(blog_title, category, blog_url, products)
    print(f"Generated {len(pins)} pin contents")

    # Step 4: Generate 10 pin images with Freepik
    print("\n[4/4] Generating 10 pin images with Freepik...")
    pins = generate_10_images(pins)

    # Add blog_number to each pin
    for pin in pins:
        pin["blog_number"] = blog_number

    # Append to queue
    queue = load_queue()
    queue["pins"].extend(pins)
    save_queue(queue)

    total = len(queue["pins"])
    pending = sum(1 for p in queue["pins"] if not p.get("posted", False))

    print(f"\n{'='*60}")
    print(f"✅ Done! Blog #{blog_number} complete")
    print(f"   Blog URL: {blog_url}")
    print(f"   Pins added: {len(pins)}")
    print(f"   Total pins in queue: {total}")
    print(f"   Pending to post: {pending}")
    print(f"\n📌 Commit pins_queue.json to GitHub to start posting!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run()
