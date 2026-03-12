"""
fix_pin_content.py — Rewrite titles & descriptions for all unposted pins in queue.
Uses Groq to batch-rewrite 10 pins per blog in one API call.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import time
from groq_gen import ask_groq

QUEUE_FILE = 'pins_queue.json'

REWRITE_PROMPT = """You are a Pinterest SEO expert targeting US home organization shoppers in 2026.

Rewrite the titles and descriptions for these {n} Pinterest pins about "{topic}".

RULES:
- "title": max 100 chars. Include "2026" OR a price OR "Amazon" in at least half the pins. Use US buyer language: "Best", "Top", "Under $X", "Worth It", "Tested", "Ranked". MUST mention "{topic}". No two pins share the same opening word.
- "description": max 500 chars. OPEN with a question: "Tired of...", "Still wasting money on...", "Looking for...". Mention "Amazon" once. Include the price {price} naturally. End with "→ Full list + Amazon links in bio!"
- "hashtags": 12 hashtags as one string. Always include: #HomeOrganization2026 #AmazonHome #AmazonFinds #OrganizationIdeas #HomeOrganization plus 7 niche tags for "{topic}".

Current pins:
{pins_json}

Return ONLY a valid JSON array of {n} objects, each with fields: pin_number, title, description, hashtags.
No markdown, no explanation."""


def rewrite_pins_for_blog(blog_number, pins):
    topic = pins[0].get('title', 'kitchen organizer')[:40]
    # Try to extract a better topic from description
    desc0 = pins[0].get('description', '')
    # Get price from description if present
    import re
    price_match = re.search(r'\$[\d.]+', desc0)
    price = price_match.group(0) if price_match else '$20'

    pins_summary = [{"pin_number": p["pin_number"], "title": p["title"], "description": p["description"][:200]} for p in pins]

    prompt = REWRITE_PROMPT.format(
        n=len(pins),
        topic=topic,
        price=price,
        pins_json=json.dumps(pins_summary, indent=2)
    )

    print(f"  Rewriting Blog #{blog_number} ({len(pins)} pins)...")
    for attempt in range(3):
        try:
            raw = ask_groq(prompt, max_tokens=4096)
            break
        except RuntimeError as e:
            if 'rate_limit' in str(e) and attempt < 2:
                print(f"  Rate limit — waiting 15s...")
                time.sleep(15)
            else:
                raise

    try:
        start = raw.find('[')
        end = raw.rfind(']') + 1
        rewrites = json.loads(raw[start:end])
        return {r['pin_number']: r for r in rewrites}
    except Exception as e:
        print(f"  [!] Parse error for Blog #{blog_number}: {e}")
        return {}


def run():
    with open(QUEUE_FILE, encoding='utf-8') as f:
        q = json.load(f)

    pins = q['pins']
    unposted = [p for p in pins if not p.get('posted')]
    print(f"Unposted pins: {len(unposted)}")

    # Group by blog_number
    from collections import defaultdict
    by_blog = defaultdict(list)
    for p in unposted:
        by_blog[p['blog_number']].append(p)

    total_fixed = 0
    for blog_num in sorted(by_blog.keys()):
        blog_pins = by_blog[blog_num]
        rewrites = rewrite_pins_for_blog(blog_num, blog_pins)

        for pin in blog_pins:
            r = rewrites.get(pin['pin_number'])
            if r:
                pin['title'] = r.get('title', pin['title'])
                hashtags = r.get('hashtags', '')
                desc = r.get('description', pin['description'].split('\n\n')[0])
                pin['description'] = desc.rstrip() + f"\n\n{hashtags}"
                total_fixed += 1

        # Save after each blog so progress isn't lost
        with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
            json.dump(q, f, indent=2, ensure_ascii=False)
        time.sleep(8)  # avoid per-minute token limit

    print(f"\nTotal pins rewritten: {total_fixed}")
    print("Sample title:", pins[6]['title'])
    print("Sample desc:", pins[6]['description'][:120])

    with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(q, f, indent=2, ensure_ascii=False)
    print("\nSaved. Run: git add pins_queue.json && git commit -m 'Improve pin titles and descriptions' && git push")


if __name__ == '__main__':
    run()
