import requests
import time
from config import FREEPIK_API_KEY, IMAGE_WIDTH, IMAGE_HEIGHT

FREEPIK_URL = "https://api.freepik.com/v1/ai/text-to-image/flux-2-pro"

def generate_image(prompt):
    """Submit image generation task to Freepik and return image URL"""
    headers = {
        "x-freepik-api-key": FREEPIK_API_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "prompt": prompt,
        "width": IMAGE_WIDTH,
        "height": IMAGE_HEIGHT,
        "prompt_upsampling": True
    }

    # Submit task
    res = requests.post(FREEPIK_URL, headers=headers, json=body)
    data = res.json()

    if "data" not in data:
        print(f"Freepik error: {data}")
        return None

    task_id = data["data"].get("task_id")
    if not task_id:
        return None

    print(f"  Freepik task submitted: {task_id}")

    # Poll until complete
    for attempt in range(30):
        time.sleep(10)
        poll = requests.get(
            f"{FREEPIK_URL}/{task_id}",
            headers={"x-freepik-api-key": FREEPIK_API_KEY}
        )
        poll_data = poll.json()
        status = poll_data.get("data", {}).get("status", "")

        if status == "completed":
            image_url = poll_data["data"]["generated"][0]["url"]
            print(f"  Image ready: {image_url[:60]}...")
            return image_url
        elif status == "failed":
            print(f"  Freepik task failed")
            return None
        else:
            print(f"  Waiting... ({attempt+1}/30) status: {status}")

    print("  Freepik timed out")
    return None


def generate_10_images(pins):
    """Generate images for all 10 pins"""
    print(f"\nGenerating {len(pins)} pin images with Freepik...")
    for i, pin in enumerate(pins):
        print(f"\nImage {i+1}/10: {pin['title'][:50]}...")
        url = generate_image(pin["freepik_prompt"])
        if url:
            pins[i]["image_url"] = url
        else:
            # Fallback: use a placeholder
            pins[i]["image_url"] = ""
            print(f"  Warning: No image for pin {i+1}")
    return pins
