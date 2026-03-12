"""
fix_pin_content.py — Rewrite titles & descriptions for all unposted pins in queue.
Uses Groq to batch-rewrite 10 pins per blog in one API call.
Fetches live blog post content for specificity (product names, prices, ratings).
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import re
import time
import requests
from groq_gen import ask_groq

QUEUE_FILE = 'pins_queue.json'

REWRITE_PROMPT = """You are a top Pinterest content strategist for US home organization. Your pins go viral because they are SPECIFIC, not generic.

BLOG TITLE: "{blog_title}"
TOPIC: "{topic}"
BLOG URL: {blog_url}

BLOG CONTENT (products, prices, ratings):
{blog_content}

CURRENT PINS TO REWRITE ({n} pins):
{pins_json}

━━━ SPECIFICITY RULE — THIS IS THE MOST IMPORTANT RULE ━━━
Generic pins fail. Specific pins go viral.

BAD (generic, NEVER write this):
  title: "Best Kitchen Shelf Organizers for 2026"
  desc: "Looking for kitchen organization ideas? Check out these great Amazon finds!"

GOOD (specific, DO write like this):
  title: "I Tested 7 Under-Shelf Baskets — This {price} One Has 47K Amazon Reviews"
  desc: "Tired of dead cabinet space? This [actual product name] ({price}, 4.7★ on Amazon) fits any shelf with zero tools. {n} picks tested, ranked from best to budget. → Full list + Amazon links in bio!"

━━━ COHERENCE RULE — MOST IMPORTANT ━━━
Title and description must tell the EXACT SAME story.
Write the title first. Then make the description reinforce it.

MATCHING EXAMPLE (DO THIS):
  title:       "I Tested 7 Under-Shelf Baskets — This $12 iDesign Has 47K Amazon Reviews"
  description: "Wasting half your cabinet space? The iDesign Under-Shelf Basket ($12, 4.7★) clips on in 30 sec — no tools. Tested all 7 picks so you don't have to. Prices from $8–$25 on Amazon. → Full list + Amazon links in bio!"

MISMATCHED EXAMPLE (NEVER DO THIS):
  title:       "Stop Wasting Money on Bad Organizers — 2026"
  description: "Looking for kitchen organization ideas? Check out these great Amazon finds!"  ← doesn't match

━━━ HARD RULES ━━━
- TITLE (max 100 chars):
  · AT LEAST 5 titles must name a SPECIFIC product from the blog content above
  · AT LEAST 5 titles must include an ACTUAL price (from the blog)
  · AT LEAST 3 titles must include a real star rating (e.g. 4.7★)
  · Must mention "{topic}" or a direct synonym in every title
  · Include "2026" OR Amazon OR a price in ≥6 titles
  · No two titles start with the same word
  · BANNED words: "great", "amazing", "awesome", "perfect" — use factual specifics instead

- DESCRIPTION (max 500 chars):
  · Must REINFORCE the exact angle set in the title (same product, same hook, same price)
  · Sentence 1: Expand the title's hook into a relatable problem statement
  · Sentence 2: Name the TOP product from the title, its actual price and star rating
  · Sentence 3: Mention how many products tested + price range
  · End EXACTLY with: "→ Full list + Amazon links in bio!"

- HASHTAGS: exactly 12 as one string. Always include:
  #HomeOrganization2026 #AmazonHome #AmazonFinds #HomeOrganization #OrganizationIdeas
  + 7 niche tags specific to "{topic}"

Return ONLY a valid JSON array of {n} objects with fields: pin_number, title, description, hashtags.
No markdown, no explanation."""


def fetch_blog_content(url, max_chars=2000):
    """Fetch blog post URL, strip HTML, return plain text summary."""
    try:
        res = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code != 200:
            return ""
        text = re.sub(r'<[^>]+>', ' ', res.text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:max_chars]
    except Exception as e:
        print(f"  [!] Could not fetch blog: {e}")
        return ""


def rewrite_pins_for_blog(blog_number, pins):
    blog_url = pins[0].get('link', '')
    blog_title = pins[0].get('title', '')

    # Derive topic from pin titles (use first pin title as base)
    topic = blog_title[:50]

    # Get price — try from descriptions first
    price = '$20'
    for p in pins:
        m = re.search(r'\$[\d.]+', p.get('description', ''))
        if m:
            price = m.group(0)
            break

    # Fetch live blog content for specificity
    print(f"  Fetching blog content from {blog_url[:60]}...")
    blog_content = fetch_blog_content(blog_url) if blog_url else ""
    if not blog_content:
        print(f"  [!] No blog content fetched — using pin descriptions as fallback")
        blog_content = " | ".join(p.get('description', '')[:100] for p in pins[:3])

    pins_summary = [
        {"pin_number": p["pin_number"], "title": p["title"], "description": p["description"][:150]}
        for p in pins
    ]

    prompt = REWRITE_PROMPT.format(
        blog_title=blog_title,
        topic=topic,
        blog_url=blog_url,
        blog_content=blog_content,
        n=len(pins),
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
    if len(pins) > 6:
        print("Sample title:", pins[6]['title'])
        print("Sample desc:", pins[6]['description'][:120])

    with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(q, f, indent=2, ensure_ascii=False)
    print("\nSaved. Run: git add pins_queue.json && git commit -m 'Improve pin titles and descriptions' && git push")


if __name__ == '__main__':
    run()
