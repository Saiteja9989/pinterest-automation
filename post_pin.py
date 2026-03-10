"""
post_pin.py — Run by GitHub Actions every 40 minutes
Picks the next unposted pin from pins_queue.json
Sends it to Make.com webhook → Pinterest posts it
"""
import json
import requests
from config import MAKE_WEBHOOK_URL

QUEUE_FILE = 'pins_queue.json'


def load_queue():
    with open(QUEUE_FILE, 'r') as f:
        return json.load(f)


def save_queue(queue):
    with open(QUEUE_FILE, 'w') as f:
        json.dump(queue, f, indent=2)


def post_to_pinterest(pin):
    """Send pin data to Make.com webhook"""
    payload = {
        "title":       pin["title"],
        "description": pin["description"],
        "image_url":   pin["image_url"],
        "link":        pin["link"],
        "board_id":    pin["board_id"]
    }
    res = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=30)
    return res.status_code == 200


def run():
    queue = load_queue()
    pins = queue.get("pins", [])

    # Find next unposted pin
    next_pin = None
    next_index = None
    for i, pin in enumerate(pins):
        if not pin.get("posted", False):
            if pin.get("image_url", ""):  # Only post if image is ready
                next_pin = pin
                next_index = i
                break

    if next_pin is None:
        print("No pending pins in queue. Add more blogs!")
        return

    print(f"\nPosting pin {next_index + 1}: {next_pin['title'][:60]}...")
    print(f"Board: {next_pin['board_id']}")
    print(f"Link:  {next_pin['link']}")

    success = post_to_pinterest(next_pin)

    if success:
        pins[next_index]["posted"] = True
        queue["pins"] = pins
        save_queue(queue)
        print("✅ Pin posted successfully!")

        # Count remaining
        remaining = sum(1 for p in pins if not p.get("posted", False))
        print(f"Pins remaining in queue: {remaining}")
    else:
        print("❌ Failed to post pin. Will retry next run.")


if __name__ == "__main__":
    run()
