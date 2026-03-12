import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests
import json

try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False

from config import GROQ_API_KEY, GROQ_MODEL, BOARDS, TOPIC_TAGS

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

WEBSITE = "smarthomeorganizing.com"

# ─── Map blog title keywords → specific room phrase for Freepik prompts ───────
TOPIC_ROOM = {
    # Kitchen sub-spaces (sorted longest-first for matching priority)
    'pantry door' : 'pantry door',
    'under sink'  : 'under-sink cabinet',
    'lazy susan'  : 'kitchen turntable cabinet',
    'food container': 'kitchen pantry',
    'refrigerator': 'refrigerator',
    'countertop'  : 'kitchen countertop',
    'countertops' : 'kitchen countertop',
    'fridge'      : 'refrigerator',
    'freezer'     : 'freezer',
    'cabinet'     : 'kitchen cabinet',
    'pantry'      : 'pantry',
    'drawer'      : 'kitchen drawer',
    'drawers'     : 'kitchen drawer',
    'counter'     : 'kitchen countertop',
    'spice'       : 'spice cabinet',
    'pot'         : 'pot and pan cabinet',
    'shelf'       : 'kitchen shelf',
    'shelves'     : 'kitchen shelf',
    # Bathroom
    'medicine'    : 'medicine cabinet',
    'makeup'      : 'makeup vanity',
    'vanity'      : 'bathroom vanity',
    'shower'      : 'shower',
    'bathroom'    : 'bathroom',
    'toilet'      : 'bathroom',
    'hair'        : 'bathroom styling station',
    # Bedroom
    'under bed'   : 'under-bed storage',
    'closet'      : 'closet',
    'wardrobe'    : 'wardrobe',
    'dresser'     : 'dresser',
    'jewelry'     : 'jewelry vanity',
    'shoe'        : 'shoe storage area',
    'bedroom'     : 'bedroom',
    # Office
    'cable'       : 'desk cable management',
    'cord'        : 'desk cord area',
    'desk'        : 'home office desk',
    'file'        : 'home office',
    # Living / Entryway
    'coffee table': 'living room',
    'entryway'    : 'entryway',
    'living room' : 'living room',
    'toy'         : 'playroom',
    'toys'        : 'playroom',
    # Laundry / Garage
    'mudroom'     : 'mudroom',
    'linen'       : 'linen closet',
    'laundry'     : 'laundry room',
    'garage'      : 'garage',
    'tool'        : 'garage tool wall',
    'bike'        : 'garage',
}

# ─── Specific visual scene for each room (used in Freepik prompts) ────────────
# Makes images look unique per blog topic instead of all being generic "kitchen"
ROOM_VISUAL = {
    'pantry door'          : 'interior view of pantry door with over-door tiered wire rack organizers holding spice jars, canned goods, and bottles in metal baskets',
    'pantry'               : 'well-stocked pantry shelves with clear labeled containers, wicker baskets, and organized canned goods on white shelving',
    'refrigerator'         : 'open refrigerator interior with clear stackable bins on glass shelves, labeled produce drawers, and neatly sorted condiments',
    'kitchen drawer'       : "bird's-eye view of organized kitchen drawer with bamboo dividers neatly separating utensils, cutlery, and gadgets",
    'spice cabinet'        : 'pull-out tiered spice drawer insert with two rows of labeled spice jars in perfect alphabetical order',
    'kitchen countertop'   : 'clean minimalist kitchen countertop with matching canisters, one appliance, and a small tray corralling oils and vinegars',
    'kitchen cabinet'      : 'open kitchen cabinet with pull-out shelf organizer, stacked matching plates, and labeled pantry containers',
    'kitchen shelf'        : 'organized floating kitchen shelf with matching labeled containers, cookbooks, and potted herb plants',
    'kitchen turntable cabinet': 'kitchen corner cabinet open showing lazy susan turntable spinning with organized condiments, oils, and spices on tiered levels',
    'under-sink cabinet'   : 'organized under-sink cabinet with two-tier sliding shelf system, labeled cleaning spray bottles, and a caddy holder',
    'pot and pan cabinet'  : 'organized deep cabinet with vertical lid holder rack, pots stacked with pan protectors, and pans hung on inner door',
    'bathroom vanity'      : 'organized bathroom vanity countertop with acrylic makeup organizer, brush holders, and skincare bottles neatly arranged',
    'makeup vanity'        : 'aesthetic makeup vanity with acrylic multi-drawer organizer, brush holder, and cosmetics displayed under warm lighting',
    'shower'               : 'clean shower corner with rust-proof wall-mounted caddy organizer holding shampoo, conditioner, and soap bars on tiered shelves',
    'bathroom'             : 'organized bathroom with labeled fabric baskets under sink, acrylic toiletry organizer on counter, and towels folded on rack',
    'medicine cabinet'     : 'open medicine cabinet interior with labeled medicine bottles in small bins, first aid supplies sorted, and vitamins in clear containers',
    'bathroom styling station': 'organized bathroom countertop with heat-resistant hair tool holder, blow dryer stored vertically, and styling products in caddy',
    'closet'               : 'organized walk-in closet with matching slim velvet hangers, labeled fabric shelf bins, and shoe rack visible on floor',
    'wardrobe'             : 'organized wardrobe interior with color-coordinated hanging clothes on matching hangers, folded sweaters on shelves, labeled bins',
    'dresser'              : "bird's-eye view of opened dresser drawer with velvet drawer dividers separating neatly folded t-shirts, socks, and underwear",
    'under-bed storage'    : 'under-bed area showing slim wheeled storage containers being pulled out, labeled by season, maximizing floor space',
    'jewelry vanity'       : 'jewelry organizer on dressing table with earring display stand, ring dish, necklace hooks, and tiered bracelet holder',
    'shoe storage area'    : 'organized shoe rack with pairs aligned by color, clear stackable shoe boxes with photo labels on front',
    'bedroom'              : 'cozy organized bedroom with nightstand organizer tray, closet partially visible showing hanging pockets and labeled bins',
    'home office desk'     : 'organized home office desk with vertical file holder, cable management box, multi-compartment desk organizer, and plant',
    'desk cable management': 'clean desk setup with all cables routed through cable management spine, velcro ties, and mounted power strip hidden from view',
    'desk cord area'       : 'desk with zero visible cords — all cables managed through cord clips, box organizer, and adhesive cable holders',
    'home office'          : 'organized home office with upright file folder organizer, labeled color-coded folders, desk drawer with supply caddy',
    'living room'          : 'organized living room with storage ottoman open showing folded blankets, floating shelves with labeled decorative baskets',
    'entryway'             : 'organized entryway with wall-mounted key hook rack, mail sorter, slim shoe rack, and labeled fabric cubby bins',
    'playroom'             : 'colorful organized playroom with labeled toy bins on low white shelves, rolling art cart, and labeled toy chest',
    'mudroom'              : 'organized mudroom with labeled cubbies for each family member, wall hooks for bags and coats, boot tray, bench storage',
    'linen closet'         : 'organized linen closet with towels folded and stacked in labeled wire bins and sheets in clear labeled storage bags',
    'laundry room'         : 'organized laundry room with wall-mounted detergent dispenser shelf, labeled sorting bins, and folding station on counter',
    'garage'               : 'organized garage with pegboard tool wall, labeled clear storage bins on metal shelving, two bikes hung on wall hooks',
    'garage tool wall'     : 'pegboard wall with outlined tool silhouettes, double-hook holders for hammers and pliers, labeled bin accessories row',
    'kitchen'              : 'organized bright white kitchen with matching labeled containers on open shelves, clear countertops, and visible organized cabinet',
}


def extract_topic(blog_title, category):
    """Return a specific room/sub-topic phrase from the blog title for image prompts.
    E.g. 'refrigerator' for fridge blog, 'kitchen drawer' for drawer blog.
    Falls back to category name if no keyword matched.
    """
    title_lower = blog_title.lower()
    # Sort by key length descending so multi-word keys match before single-word
    for keyword in sorted(TOPIC_ROOM.keys(), key=len, reverse=True):
        if keyword in title_lower:
            return TOPIC_ROOM[keyword]
    return category


def get_room_visual(room):
    """Return a specific visual scene description for the room, for Freepik image prompts."""
    return ROOM_VISUAL.get(room, f'beautifully organized {room} with labeled clear containers and neat storage bins')


def _get_style_definitions_UNUSED(room, category, n_products, n1, n2, n3, pr1, pr2, pr3, r1, r2, r3):
    """UNUSED — kept for reference only."""
    cat_t = category.title()
    room_t = room.title()
    cat_u = category.upper()
    room_visual = get_room_visual(room)
    return [
        # 0: LIFESTYLE PHOTO
        {
            "name": "LIFESTYLE PHOTO",
            "title_rule": (
                f'MUST start with a number. Use "{room_t}" specifically — NOT generic "{cat_t} organizer". '
                f'Angle: "N Best {room_t}s for [SPECIFIC BENEFIT] — 2026 Amazon Picks". '
                f'image_headline must say "{room_t.upper()} PICKS" or similar — never just "KITCHEN ORGANIZATION".'
            ),
            "freepik": (
                f'Lifestyle interior photography Pinterest pin, portrait 2:3 ratio. '
                f'Real interior photo showing {room_visual}, '
                f'warm natural window light, shot from slightly above at 45 degree angle. '
                f'Dark semi-transparent gradient overlay on bottom 40% of image. '
                f'Bold white sans-serif text reading \'[6-WORD HEADLINE]\' centered on overlay. '
                f'Smaller white subtext below reading \'STEP BY STEP GUIDE INSIDE\'. '
                f'Dark navy blue bar at very bottom with white text \'smarthomeorganizing.com\'. '
                f'Sharp focus, high resolution, real home interior, lifestyle photography.'
            ),
        },
        # 1: COMPARISON RANKED
        {
            "name": "COMPARISON RANKED",
            "title_rule": (
                f'MUST start with "How to Choose" or "Which". '
                f'Reference the SPECIFIC product type from the blog (e.g. "spice drawer insert", "pull-out fridge bin"). '
                f'Angle: comparison/decision-helper framing. Must feel different from other blogs.'
            ),
            "freepik": (
                f'Pinterest pin graphic design poster, portrait 2:3 ratio, clean pure white background. '
                f'Bold black sans-serif headline text at top reading \'[6-WORD HEADLINE]\'. '
                f'Three {room} organizer product images stacked vertically center-aligned with clear spacing. '
                f'Gold circular badge overlaid on product 1 with text \'#1 BEST {pr1}\'. '
                f'Gold badge on product 2 \'#2 TOP VALUE {pr2}\'. '
                f'Gold badge on product 3 \'#3 BUDGET {pr3}\'. '
                f'Row of 5 yellow star icons beside each product. '
                f'Dark navy blue footer bar at bottom with white text \'smarthomeorganizing.com\'. '
                f'Professional product comparison infographic.'
            ),
        },
        # 2: STOP HOOK
        {
            "name": "STOP HOOK",
            "title_rule": (
                f'MUST start with "Stop" or "Never". '
                f'Name a SPECIFIC mistake people make with {room_t}s (e.g. "Stop Buying {room_t}s That Waste Space", "Never Use This {room_t} Trick Again"). '
                f'image_headline must start with STOP or NEVER and mention {room_t.upper().split()[0]}. Do NOT write "BAD KITCHEN ORGANIZERS".'
            ),
            "freepik": (
                f'Pinterest pin graphic poster, portrait 2:3 ratio. '
                f'Bold bright red full-width banner at top with large white Impact font text reading \'STOP!\'. '
                f'Clean white background below. Bold black uppercase text reading \'[5-WORD WARNING HEADLINE]\'. '
                f'Three product images in a horizontal row center. '
                f'Bold black text \'WE TESTED {n_products} ON AMAZON\'. '
                f'Dark navy blue footer \'smarthomeorganizing.com\'. '
                f'High contrast urgent graphic design style.'
            ),
        },
        # 3: TIPS LIST
        {
            "name": "TIPS LIST",
            "title_rule": (
                f'MUST start with a number + "Tips", "Secrets", or "Hacks". '
                f'Focus specifically on {room_t}s (e.g. "7 {room_t} Hacks That Actually Work", "5 Secrets to a Clutter-Free {room_t}"). '
                f'image_headline must reference {room_t.upper().split()[0]} — not generic KITCHEN HACKS.'
            ),
            "freepik": (
                f'Pinterest pin design, portrait 2:3 ratio. '
                f'Top 40% real interior photo of beautifully organized {room} with clear containers, natural light. '
                f'Bottom 60% clean white section. Bold dark navy sans-serif headline \'[5-WORD TIPS HEADLINE]\'. '
                f'Clean numbered list in dark text: \'1. [SPECIFIC TIP]\', \'2. [SPECIFIC TIP]\', \'3. [SPECIFIC TIP]\'. '
                f'Dark navy footer bar \'smarthomeorganizing.com\'. Minimal clean editorial design.'
            ),
        },
        # 4: BEFORE/AFTER
        {
            "name": "BEFORE/AFTER",
            "title_rule": (
                f'MUST start with "I" — first-person transformation story. '
                f'Mention the SPECIFIC product from this blog and actual price {pr1}. '
                f'Angle: personal experience with THIS exact product type. Different from "I organized my kitchen" — be specific.'
            ),
            "freepik": (
                f'Pinterest pin lifestyle photography, portrait 2:3 ratio. '
                f'Vertical split design. Top half: cluttered messy {room} interior, items piled randomly, '
                f'poor organization, real interior photo. Bold red rounded label \'BEFORE\' top-left. '
                f'Bottom half: same {room} beautifully organized, clear labeled bins, everything in place, '
                f'warm light, real interior photo. Bold green label \'AFTER\' bottom-left. '
                f'Bold white text centered on divider reading \'THIS {pr1} AMAZON PRODUCT DID THIS\'. '
                f'Dark navy footer \'smarthomeorganizing.com\'. Real interior photography.'
            ),
        },
        # 5: DARK MOODY
        {
            "name": "DARK MOODY",
            "title_rule": (
                f'MUST be aspirational/aesthetic/emotional. No numbers. '
                f'Paint a visual dream specifically around the {room_t} (e.g. "The {room_t} That Changed My Mornings", "Your Dream {room_t} Starts Here"). '
                f'image_headline must mention {room_t.upper().split()[0]} — NEVER write "DREAM KITCHEN AESTHETIC" or generic kitchen text.'
            ),
            "freepik": (
                f'Pinterest pin cinematic interior photography, portrait 2:3 ratio. '
                f'Dramatic dark moody scene: {room_visual}, shot with dark charcoal walls and warm amber accent lighting. '
                f'Deep shadows on sides, warm golden light highlighting the organized storage. Dark atmospheric aesthetic. '
                f'Large bold white sans-serif headline centered \'[6-WORD ASPIRATIONAL HEADLINE]\'. '
                f'Small gold italic text below \'Full Amazon links inside\'. '
                f'Dark navy footer \'smarthomeorganizing.com\'. '
                f'Cinematic editorial photography, dramatic shadows, high contrast, moody interior.'
            ),
        },
        # 6: BUDGET PRICE
        {
            "name": "BUDGET PRICE",
            "title_rule": (
                f'MUST lead with a price, deal, or budget angle using the actual cheapest product price. '
                f'Name the SPECIFIC product type, not generic "{room_t} organizer". '
                f'Angle: "N [SPECIFIC PRODUCT TYPE] Under {pr1} That Actually Work — 2026 Amazon Finds".'
            ),
            "freepik": (
                f'Pinterest pin graphic design, portrait 2:3 ratio, bright white background. '
                f'Large bold bright red circle badge at top center with white text \'ONLY {pr1}\' in large Impact font. '
                f'Organized {room} photo below the badge, natural lighting, clear bins visible. '
                f'Bold black sans-serif text \'[5-WORD DEAL HEADLINE]\'. '
                f'Row of 5 solid yellow star icons. Small dark text \'{r1}/5 stars from Amazon buyers\'. '
                f'Dark navy footer \'smarthomeorganizing.com\'. Eye-catching deal graphic design.'
            ),
        },
        # 7: AUTHORITY RANKED — dark editorial magazine style (visually distinct from lifestyle)
        {
            "name": "AUTHORITY RANKED",
            "title_rule": (
                f'MUST lead with credibility — review count, Amazon ranking, or expert testing. '
                f'Name the SPECIFIC product from this blog. '
                f'Angle: "N [SPECIFIC PRODUCT] Ranked by Thousands of Amazon Buyers" or "We Tested Every [PRODUCT] on Amazon — Here Are the Winners".'
            ),
            "freepik": (
                f'Pinterest pin editorial magazine cover graphic design, portrait 2:3 ratio. '
                f'Dark charcoal slate background, NO white background, NO lifestyle photo. '
                f'Bold large white serif headline at top: \'[3-WORD HEADLINE]\'. '
                f'Thin horizontal gold divider line below headline. '
                f'Center panel: three {room} organizer product photographs on dark background with soft studio lighting and drop shadows. '
                f'Gold award ribbon badge overlaid on center product reading \'AMAZON #1 PICK 2026\'. '
                f'White bold ranking text below: \'1 — BEST OVERALL  2 — BEST VALUE  3 — BUDGET PICK\'. '
                f'Row of 5 filled gold star icons with text \'RANKED BY {r1}★ VERIFIED REVIEWS\'. '
                f'Dark navy footer bar: \'smarthomeorganizing.com\'. '
                f'Premium dark editorial magazine aesthetic, no white space, high contrast typography.'
            ),
        },
        # 8: PROBLEM/SOLUTION
        {
            "name": "PROBLEM/SOLUTION",
            "title_rule": (
                f'MUST start with "Why Your". '
                f'Name a SPECIFIC problem with {room_t}s (e.g. "Why Your {room_t} Is Always a Mess", "Why Your {room_t} Is Causing Food Waste"). '
                f'image_headline must reference {room_t.upper().split()[0]} — not generic MESSY KITCHEN.'
            ),
            "freepik": (
                f'Pinterest pin editorial graphic design, portrait 2:3 ratio, cream off-white background. '
                f'Bold red full-width top bar white text \'THE PROBLEM:\'. '
                f'Bold black text \'[5-WORD PROBLEM STATEMENT]\'. Thin red horizontal divider line. '
                f'Bold forest green full-width bar white text \'THE SOLUTION:\'. '
                f'Real interior photo of organized {room}, clear bins, neat labels. '
                f'Three bullet points below photo in clean dark typography: '
                f'\'• {n1[:20]} {pr1}\', \'• {n2[:20]} {pr2}\', \'• {n3[:20]} {pr3}\'. '
                f'Dark navy footer \'smarthomeorganizing.com\'. Clean editorial poster.'
            ),
        },
        # 9: SOCIAL PROOF
        {
            "name": "SOCIAL PROOF",
            "title_rule": (
                f'MUST start with a star rating ({r1}★) or "Amazon Verified" or review count. '
                f'Name THIS blog\'s specific top product ({n1[:30]}). '
                f'Angle: social proof + specific product, not generic. E.g. "{r1}★ — This {pr1} [SPECIFIC PRODUCT] Has 10,000 Five-Star Reviews for a Reason".'
            ),
            "freepik": (
                f'Pinterest pin trust graphic design, portrait 2:3 ratio. '
                f'Bright orange full-width top banner white text \'★ AMAZON VERIFIED ★\'. '
                f'Dark {room} interior photo background with dark overlay for text readability. '
                f'Bold large white sans-serif headline \'[6-WORD SOCIAL PROOF HEADLINE]\'. '
                f'Large yellow star rating graphic \'{r1} / 5 STARS\'. '
                f'White text list: \'{n1[:25]}\', \'{n2[:25]}\', \'{n3[:25]}\'. '
                f'Bright red rounded rectangle button graphic with white text \'FULL GUIDE + AMAZON LINKS\'. '
                f'Dark navy footer \'smarthomeorganizing.com\'. Trust and authority graphic.'
            ),
        },
    ]


def get_trending_keywords(topic, category):
    """Fetch trending keywords: Google Suggest (always) + pytrends (if available)"""
    suggestions = []
    seen = set()

    # 1. Google Suggest — always works, no key needed
    queries = [
        f"best {category} organizer 2026",
        f"best {category} organization ideas",
        f"amazon {category} organizer",
    ]
    for q in queries[:2]:
        try:
            url = "https://suggestqueries.google.com/complete/search"
            params = {"client": "firefox", "hl": "en", "gl": "us", "q": q}
            res = requests.get(url, params=params, timeout=6)
            for s in res.json()[1][:6]:
                s = s.strip()
                if s and s not in seen:
                    suggestions.append(s)
                    seen.add(s)
        except Exception:
            pass

    # 2. pytrends — richer related queries (US, last 7 days)
    if PYTRENDS_AVAILABLE and len(suggestions) < 8:
        try:
            pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
            kw = f"{category} organizer"
            pytrends.build_payload([kw], timeframe='now 7-d', geo='US')
            related = pytrends.related_queries()
            if kw in related and related[kw].get('top') is not None:
                for _, row in related[kw]['top'].head(5).iterrows():
                    q = str(row['query']).strip()
                    if q and q not in seen:
                        suggestions.append(q)
                        seen.add(q)
        except Exception as e:
            print(f"  pytrends skipped: {e}")

    return suggestions[:10]


def ask_groq(prompt, max_tokens=4096, json_mode=False):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": max_tokens
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    res = requests.post(GROQ_URL, headers=headers, json=body)
    data = res.json()
    if "choices" not in data:
        print(f"    Groq API error: {data}")
        raise RuntimeError(f"Groq API error: {data.get('error', data)}")
    return data["choices"][0]["message"]["content"]


BLOG_INTRO_HOOKS = [
    # Hook 0 — Problem/frustration opener (standard)
    "Hook with a relatable frustration the reader faces right now. Use <strong> for key phrases. End paragraph 2 with: \"I spent hours researching the top-rated, most-reviewed products on Amazon to bring you this ranked list.\"",
    # Hook 1 — Personal story opener
    "Open with a short first-person story: 'Last month I finally tackled my [specific space]...' Make it relatable and conversational. Reveal the solution at the end of paragraph 2. End with: \"After testing and reading thousands of Amazon reviews, here are the only products worth your money.\"",
    # Hook 2 — Surprising statistic or question opener
    "Open with a surprising question or bold statement (e.g. 'Most people waste $40 on [product] that breaks in 3 months.'). Build tension in paragraph 1. End paragraph 2 with: \"I ranked every top-rated option on Amazon so you don't have to waste another dollar.\"",
]

def generate_blog_html(blog_title, category, products, blog_number=1):
    """Generate full SEO-optimized blog post HTML matching professional style"""
    n = len(products)
    product_list = "\n".join([
        f"- #{i+1}: {p['name']} | Price: {p['price']} | Rating: {p['rating']} stars | Affiliate Link: {p['affiliate_link']} | Image URL: {p['image_url']}"
        for i, p in enumerate(products)
    ])

    comparison_rows = "\n".join([
        f"  - {p['name']} | Best For: [use case] | {p['price']} | {p['rating']}★"
        for p in products
    ])

    intro_hook = BLOG_INTRO_HOOKS[blog_number % len(BLOG_INTRO_HOOKS)]

    prompt = f"""You are a senior affiliate content writer for a US home organization blog. Write a complete, professional, SEO-optimized blog post that ranks on Google and converts Amazon clicks.

Blog Title: "{blog_title}"
Target keywords: {blog_title.lower()}, best {category} organizers 2026, amazon {category} organizers
Products ({n} total):
{product_list}

Audience: US homeowners aged 28-55, shopping on Amazon, value-conscious, want honest recommendations.
Tone: Friendly expert — like a knowledgeable friend who tested everything, not a generic AI list.
Updated: March 2026

---SECTION 1: AFFILIATE DISCLOSURE---
<div style="background:#fff8e1;border-left:4px solid #ffc107;padding:14px 18px;margin:24px 0;border-radius:6px;font-size:14px"><strong>Disclosure:</strong> This post contains affiliate links. As an Amazon Associate I earn from qualifying purchases at no extra cost to you. I only recommend products I've researched thoroughly.</div>

---SECTION 2: INTRO (3 paragraphs, 150-200 words total)---
{intro_hook}
- Paragraph 1: {intro_hook} Use <strong> for 2-3 key phrases. Open with a relatable problem US homeowners face.
- Paragraph 2: Brief context — why this category matters in 2026, mention "Amazon" naturally.
- Paragraph 3: End with: "I spent hours researching thousands of Amazon reviews to bring you this ranked list — updated March 2026."
Do NOT write generic filler. Every sentence must earn its place.

---SECTION 3: QUICK ANSWER BOX---
<div style="background:#e3f2fd;border-left:5px solid #1976d2;padding:16px 20px;margin:24px 0;border-radius:6px">
<strong>Quick Answer (2026):</strong> The best overall pick is the <strong>[Product #1 name]</strong> — [one sharp sentence: what makes it stand out, mention price and rating]. Budget pick: <strong>[Product #2 or cheapest]</strong> at [price]. Premium pick: <strong>[most expensive product]</strong>.
</div>

---SECTION 4: BUYING GUIDE — WHAT TO LOOK FOR (H2)---
<h2>What to Look for in a {blog_title.split("—")[0].strip()} (2026 Buyer's Guide)</h2>
Write 4 buying criteria specific to this product type. Each as:
<h3>[Criterion Name]</h3>
<p>[2-3 sentences explaining why it matters and what to look for. Be specific — mention measurements, materials, or real scenarios.]</p>

---SECTION 5: COMPARISON TABLE (H2)---
<h2>All {n} Picks at a Glance</h2>
<div style="overflow-x:auto">
<table style="width:100%;border-collapse:collapse;margin:20px 0;font-size:15px">
<thead><tr style="background:#1976d2;color:#fff;text-align:left">
<th style="padding:12px 14px">#</th><th style="padding:12px 14px">Product</th><th style="padding:12px 14px">Best For</th><th style="padding:12px 14px">Price</th><th style="padding:12px 14px">Rating</th>
</tr></thead>
<tbody>
[For each product — alternate row background #ffffff and #f5f5f5, padding 11px 14px. Include rank number, product name, specific best-for use case, price, rating with ★ symbol]
</tbody>
</table>
</div>

---SECTION 6: PRODUCT REVIEWS — repeat for ALL {n} products---
Ranking labels: #1=Best Overall, #2=Best Value, #3=Best Premium, #4+=Best for [specific use case]

For EACH product use this EXACT structure:

<h2>#[N] — [Ranking Label]: [Product Name]</h2>
<img src="[EXACT image_url]" style="float:right;width:240px;margin:0 0 16px 24px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.12)" alt="[product name]">
<p>[Opening sentence with the product's #1 standout feature — be specific: mention a real measurement, material, or capacity. e.g. "This expandable bamboo organizer stretches from 13 to 21 inches to fit virtually any standard kitchen drawer."]</p>
<p>[Second sentence: mention who it's best for and one real-world use case. Third sentence: reference real Amazon buyer feedback naturally.]</p>
<p><strong>Best for:</strong> [Very specific person/scenario — e.g. "Renters with small kitchen drawers who need a tool-free, damage-free solution"]</p>
<h3>Pros</h3>
<ul>
<li>[Pro 1 — specific feature with measurement or material: e.g. "Expands from 13\" to 21\" — fits most standard kitchen drawers"]</li>
<li>[Pro 2 — practical benefit: e.g. "Natural bamboo resists moisture and odors better than plastic"]</li>
<li>[Pro 3 — value/convenience: e.g. "Tool-free install — just place it in the drawer"]</li>
<li>[Pro 4 — unique differentiator vs competitors]</li>
<li>[Pro 5 — buyer-confirmed detail from reviews]</li>
</ul>
<h3>Cons</h3>
<ul>
<li>[Honest con — real limitation, not vague: e.g. "Bamboo can warp if left wet for extended periods"]</li>
<li>[Second honest con — e.g. "Fixed compartments may not fit large cooking utensils over 12 inches"]</li>
</ul>
<div style="background:#f9f9f9;border:1px solid #e0e0e0;border-radius:6px;padding:14px 18px;margin:16px 0">
<strong>Bottom Line:</strong> [1 punchy sentence — who should buy this and why it's worth the price. Mention the price.]
</div>
<p style="color:#555;font-size:15px"><strong>Price:</strong> [price] &nbsp;|&nbsp; <strong>Rating:</strong> [rating]★ &nbsp;|&nbsp; <strong>Reviews:</strong> [estimated],000+ on Amazon</p>
<div style="clear:both"></div>
<div style="text-align:center;margin:24px 0">
<a href="[EXACT affiliate_link]" style="background:#ff9900;color:#fff;padding:13px 28px;border-radius:6px;text-decoration:none;display:inline-block;font-weight:700;font-size:16px;letter-spacing:0.3px">Check Price on Amazon</a>
</div>
<hr style="margin:32px 0;border:none;border-top:1px solid #ececec">

---SECTION 7: PRO TIPS (H2)---
<h2>5 Pro Tips to Get the Most Out of Your {category.title()} Organizer</h2>
<ol>
[5 actionable, specific tips. Each: <li><strong>[Tip Name]:</strong> [2 sentences — practical, US-household specific, not generic]</li>]
</ol>

---SECTION 8: FAQ (H2) — for Google featured snippets---
<h2>Frequently Asked Questions</h2>
Write 5 Q&A pairs. Questions must be phrased exactly how a US buyer would type them into Google.
Format each as:
<h3>[Full question as someone would Google it]</h3>
<p>[Answer: 3-4 sentences minimum. Be specific. Include measurements, price ranges, or comparisons where relevant. Google rewards detailed answers for featured snippets.]</p>

---SECTION 9: FINAL VERDICT (H2)---
<h2>Final Verdict — Which One Should You Buy?</h2>
<p>[Paragraph 1: Recommend #1 for most people — say exactly why in 2 sentences.]</p>
<p>[Paragraph 2: Who should pick #2 (budget) vs #3 (premium) — be specific.]</p>
<p>[Paragraph 3: Motivating close — 1-2 sentences about how this small purchase makes a real difference in daily life.]</p>

---SECTION 10: QUICK SHOP — ALL PICKS---
<h2>Shop All {n} Picks on Amazon</h2>
<ol>
[For each product: <li><a href="[EXACT affiliate_link]" style="color:#1976d2;font-weight:600">[Product Name]</a> — [3-4 word best-for label] — [price]</li>]
</ol>

---SECTION 11: DISCLAIMER---
<p style="font-size:13px;color:#888;margin-top:32px;border-top:1px solid #eee;padding-top:16px">Last updated: March 2026. As an Amazon Associate I earn from qualifying purchases. Prices are approximate and subject to change — always verify on Amazon before purchasing.</p>

HARD REQUIREMENTS:
- US English only. Conversational but expert tone. No fluff, no filler sentences.
- Return ONLY the HTML body content — no html/head/body tags, no markdown fences, no explanation
- Use EXACT image_url and affiliate_link values from the product list — never invent URLs
- Word count: 2500-3200 words
- Use "2026" at least 4 times naturally throughout
- CRITICAL: ALL 11 SECTIONS must be present and complete — never stop early
- CRITICAL: Every product gets EXACTLY 5 pros and EXACTLY 2 cons — all specific, none generic
- CRITICAL: Zero author names, bylines, or attributions anywhere"""

    return ask_groq(prompt, max_tokens=8192)




def generate_pin_content(blog_title, category, blog_url, products, blog_number=1, blog_html=None):
    """Generate 10 Pinterest pins by having Groq analyze the blog and invent
    the best-suited pin concepts for that specific blog. No fixed template list.
    Each pin gets: title, description, text_on_pin, and a detailed Flux image prompt.
    """
    import re as _re
    board_id = BOARDS.get(category, BOARDS['general'])
    n_products = len(products)

    room = extract_topic(blog_title, category)
    room_visual = get_room_visual(room)
    print(f"  Topic detected: '{room}' (from blog title)")

    # Fetch trending keywords
    print("  Fetching trending keywords for SEO...")
    trending = get_trending_keywords(blog_title, category)
    trending_str = ", ".join(f'"{kw}"' for kw in trending) if trending else f'"best {category} organizer 2026"'

    # Strip blog HTML to plain text (max 3000 chars)
    blog_text = ""
    if blog_html:
        blog_text = _re.sub(r'<[^>]+>', ' ', blog_html)
        blog_text = _re.sub(r'\s+', ' ', blog_text).strip()[:3000]

    # Build product details with all fields Groq needs for specificity
    product_details = "\n".join([
        f"  P{i+1}: \"{p.get('name','')[:60]}\" | {p.get('price','?')} | {p.get('rating','?')}★"
        for i, p in enumerate(products)
    ])

    prompt = f"""You are a Pinterest marketing expert and Flux Pro 2 image prompt engineer.
Niche: Smart Home Organization. Website: {WEBSITE}

━━━ READ THIS BLOG ━━━
BLOG TITLE: "{blog_title}"
BLOG URL: {blog_url}
SPACE: "{room}" | CATEGORY: {category}
TRENDING: {trending_str}

PRODUCTS ({n_products} total):
{product_details}

BLOG CONTENT:
{blog_text}

BASE VISUAL SCENE (use as foundation for all image prompts):
"{room_visual}"

━━━ STEP 1: ANALYZE WHAT THIS BLOG CONTAINS ━━━
Check only what is ACTUALLY in this blog:
- step-by-step process / tutorial
- before & after / transformation
- product ranking / comparison
- specific product spotlight
- budget / price reveal
- pro tips / hacks
- common mistakes / what to avoid
- time-saving benefit
- review count / social proof
- zone method / organizational system

━━━ STEP 2: INVENT 10 PIN CONCEPTS BASED ON WHAT YOU FOUND ━━━
Rules:
- Each pin must come from REAL content in this blog — if the blog has no before/after, don't make one
- Every pin feels like it belongs ONLY to this blog
- Mix emotional angles: urgency / social proof / aspiration / education / curiosity / ranking / price shock / personal story / question / tip
- No two pins share the same opening word in the title
- AT LEAST 5 pins name a real product from the list above
- AT LEAST 5 pins include an actual price from the list
- AT LEAST 3 pins include a real star rating
- BANNED words: "great", "amazing", "awesome", "perfect"

━━━ STEP 3: FOR EACH PIN WRITE ALL 5 FIELDS ━━━

"pin_number": 1-10

"pin_idea": What this pin is about — one line

"why_this_pin": Why this concept fits THIS specific blog — one line

"pinterest_title": SEO title, max 100 chars. Must make someone stop scrolling and click.
  Must reference "{room}" or a direct synonym. Include price OR "Amazon" OR "2026" in ≥6 titles.

"pinterest_description": 2-3 sentences + 5 hashtags at the end.
  Sentence 1: Expand the title's hook — same product, same price, same angle.
  Sentence 2: Supporting detail (review count / comparison / pro tip from the blog).
  Sentence 3: "Tap to see all {n_products} picks with Amazon links."
  End with: #HomeOrganization2026 #AmazonHome + 3 more niche hashtags.

"text_on_pin": Exact words rendered ON the image by Flux.
  Max 3 lines. Max 4-5 words per line. ALL CAPS. Simple common English. Must match the title's hook.
  {{"line1": "MAIN HOOK", "line2": "SUPPORTING TEXT", "line3": "", "website": "{WEBSITE}"}}

"flux_prompt": Complete Flux Pro 2 image generation prompt. Must produce a FULL Pinterest pin with text rendered on it.
  Write it in this exact structure:

  PART 1 FORMAT: "A professional Pinterest pin image, vertical format, 2:3 aspect ratio, 1000x1440 pixels."
  PART 2 LAYOUT: Describe where the photo is and where the text area is (e.g. "full bleed photo top 65%, dark gradient text banner bottom 35%").
  PART 3 SCENE: Start from the base scene: "{room_visual}". Then add what is SPECIFIC to this pin's angle:
    - Exact product type visible (material, color, size)
    - What is inside/around it
    - Camera angle: overhead / eye-level / 45° / close-up
    - Lighting: "warm morning sunlight from left window" / "soft diffused studio light, white walls" / "golden hour side-lighting"
  PART 4 TEXT ON IMAGE (Flux renders this):
    - Dark semi-transparent gradient overlay on bottom 35%
    - text reads exactly "[LINE1 from text_on_pin]" — large bold white Impact/sans-serif font, centered
    - text reads exactly "[LINE2 from text_on_pin]" — smaller white font below
    - text reads exactly "{WEBSITE}" — small white font at bottom
  PART 5 STYLE: "Photorealistic interior lifestyle photography, Canon 5D, 35mm lens, shallow depth of field, 8K sharp, clean composition. No watermarks, no people, no text outside the designated text area, Pinterest vertical format."

  EXAMPLE of a good flux_prompt:
  "A professional Pinterest pin image, vertical format, 2:3 aspect ratio, 1000x1440 pixels. Layout: full bleed photo top 65%, dark gradient text banner bottom 35%. Scene: white modern kitchen cabinet, iDesign wire under-shelf basket clipped to underside of white wood shelf, holding small olive oil bottles and spice jars neatly arranged, warm morning sunlight streaming from left window, soft shadow on wall behind, camera angle slightly below eye-level looking up at basket, 35mm lens shallow depth of field. Dark semi-transparent gradient overlay on bottom 35%, text reads exactly 'TESTED: 7 SHELF BASKETS' in large bold white Impact font centered, text reads exactly '$12 · 4.7★ on Amazon' in smaller white font below, text reads exactly 'smarthomeorganizing.com' in small white font at bottom. Photorealistic interior lifestyle photography, Canon 5D, 8K sharp, clean composition. No watermarks, no people, no text outside the banner, Pinterest vertical format."

Return valid JSON in this exact format:
{{
  "blog_analysis": {{
    "blog_topic": "topic in 5 words",
    "blog_contains": ["content type 1", "content type 2"],
    "primary_keywords": ["kw1", "kw2", "kw3"]
  }},
  "pins": [
    {{
      "pin_number": 1,
      "pin_idea": "...",
      "why_this_pin": "...",
      "pinterest_title": "...",
      "pinterest_description": "...",
      "text_on_pin": {{"line1": "...", "line2": "...", "line3": "", "website": "{WEBSITE}"}},
      "flux_prompt": "..."
    }}
  ]
}}"""

    raw = ask_groq(prompt, max_tokens=8192, json_mode=True)

    # Parse response
    try:
        data = json.loads(raw)
        pins_data = data.get('pins', [])
        analysis = data.get('blog_analysis', {})
        print(f"  Blog topic: {analysis.get('blog_topic', '')}")
        print(f"  Content types: {', '.join(analysis.get('blog_contains', [])[:5])}")
    except Exception as e:
        print(f"  [!] JSON parse error: {e}")
        pins_data = []

    topic_tags = TOPIC_TAGS.get(category, TOPIC_TAGS["general"])

    pins = []
    for i, pin in enumerate(pins_data):
        pins.append({
            "pin_number":     i + 1,
            "style":          pin.get("pin_idea", ""),
            "title":          pin.get("pinterest_title", ""),
            "description":    pin.get("pinterest_description", ""),
            "freepik_prompt": pin.get("flux_prompt", ""),
            "link":           blog_url,
            "board_id":       board_id,
            "topic_tags":     topic_tags,
            "category":       category,
            "image_url":      "",
            "posted":         False
        })

    return pins
