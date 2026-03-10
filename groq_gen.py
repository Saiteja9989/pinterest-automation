import requests
import json
from config import GROQ_API_KEY, GROQ_MODEL, BOARDS

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def ask_groq(prompt):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    res = requests.post(GROQ_URL, headers=headers, json=body)
    return res.json()["choices"][0]["message"]["content"]


def generate_blog_html(blog_title, category, products):
    """Generate full SEO-optimized blog post HTML"""
    product_list = "\n".join([
        f"- Product {i+1}: {p['name']} | Price: {p['price']} | Rating: {p['rating']} | Link: {p['affiliate_link']} | Image: {p['image_url']}"
        for i, p in enumerate(products)
    ])

    prompt = f"""You are an expert affiliate blog writer targeting US audience.
Write a complete, SEO-optimized blog post for: "{blog_title}"

Products to include:
{product_list}

Requirements:
- Write in US English
- Full HTML (no <html><head><body> tags, just content tags)
- Include: intro paragraph, each product with image (float:right, width:250px), description, pros/cons, buy button with affiliate link
- Buy button style: background #ff9900, color white, padding 10px 20px, border-radius 5px, text-decoration none
- Include comparison table of all products at the end
- Include FAQ section (5 questions)
- Include disclaimer at very end: "As an Amazon Associate, I earn from qualifying purchases."
- Total length: 1500-2000 words
- Use H2 for product titles, H3 for sections
- Target keywords: {blog_title.lower()}, best organizers, amazon organizers 2026

Return ONLY the HTML content, no explanation."""

    return ask_groq(prompt)


def generate_pin_content(blog_title, category, blog_url, products):
    """Generate 10 pin titles, descriptions, hashtags and Freepik prompts"""
    product_names = ", ".join([p['name'] for p in products[:3]])
    board_id = BOARDS.get(category, BOARDS['general'])

    prompt = f"""You are a Pinterest SEO expert targeting US audience (home organization niche).
Blog title: "{blog_title}"
Top products: {product_names}
Blog URL: {blog_url}

Generate exactly 10 Pinterest pins. Each pin must be different style:
Pin 1: Problem/Solution style
Pin 2: List style ("9 Best...")
Pin 3: Budget focus ("Under $30")
Pin 4: Transformation ("Before/After")
Pin 5: Tips style ("5 Tips...")
Pin 6: Urgency ("Must Have in 2026")
Pin 7: Story style ("I Tried...")
Pin 8: Expert style ("Pro Organizers Say...")
Pin 9: Seasonal ("Spring Cleaning...")
Pin 10: Comparison ("vs. Other Options")

For each pin return JSON with:
- title (max 100 chars, SEO optimized)
- description (max 500 chars, include keywords + call to action)
- hashtags (10 relevant hashtags)
- freepik_prompt (detailed image prompt for a Pinterest pin 1000x1500px showing organized home space, NO TEXT in image, photorealistic, bright, clean aesthetic)

Return ONLY a valid JSON array of 10 objects. No explanation."""

    raw = ask_groq(prompt)

    # Extract JSON from response
    try:
        start = raw.find('[')
        end = raw.rfind(']') + 1
        pins_data = json.loads(raw[start:end])
    except:
        pins_data = []

    # Add board_id and blog_url to each pin
    pins = []
    for i, pin in enumerate(pins_data):
        pins.append({
            "pin_number": i + 1,
            "title": pin.get("title", ""),
            "description": pin.get("description", "") + f"\n\n{pin.get('hashtags', '')}",
            "freepik_prompt": pin.get("freepik_prompt", ""),
            "link": blog_url,
            "board_id": board_id,
            "image_url": "",   # filled by freepik_gen.py
            "posted": False
        })

    return pins
