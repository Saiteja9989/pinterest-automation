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

# ─── Category-based style rotation ────────────────────────────────────────────
# Indices 0-9 map to style definitions (0=lifestyle,1=comparison,2=stop,
# 3=tips,4=before/after,5=dark moody,6=budget,7=authority,8=problem,9=social)
STYLE_ORDERS = {
    'kitchen':  [2, 1, 4, 6, 0, 7, 8, 3, 9, 5],  # STOP hook leads (urgency)
    'bathroom': [0, 3, 1, 9, 4, 6, 5, 2, 7, 8],  # Lifestyle leads (aspirational)
    'bedroom':  [0, 5, 4, 9, 1, 3, 6, 7, 8, 2],  # Lifestyle + dark moody
    'spring':   [4, 3, 0, 8, 2, 9, 1, 6, 5, 7],  # Before/after leads (transformation)
    'office':   [3, 1, 6, 7, 8, 2, 0, 5, 9, 4],  # Tips leads (productivity)
    'living':   [0, 1, 4, 9, 5, 8, 3, 6, 7, 2],  # Lifestyle leads
    'kids':     [9, 3, 8, 1, 4, 0, 6, 7, 2, 5],  # Social proof leads
    'laundry':  [4, 0, 3, 8, 1, 6, 9, 5, 2, 7],  # Before/after leads
    'garage':   [7, 2, 1, 8, 6, 3, 4, 0, 5, 9],  # Authority leads
    'budget':   [6, 2, 9, 8, 1, 3, 4, 0, 5, 7],  # Budget price leads
    'general':  [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
}

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


def get_style_definitions(room, category, n_products, n1, n2, n3, pr1, pr2, pr3, r1, r2, r3):
    """Return 10 style dicts indexed 0-9, each with name, title_rule, freepik template."""
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


def ask_groq(prompt, max_tokens=4096):
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

    prompt = f"""You are an expert affiliate blog writer for US audience. Write a complete SEO-optimized blog post.

Blog Title: "{blog_title}"
Number of products: {n}

Products:
{product_list}

Write the blog in EXACTLY this structure with EXACTLY this HTML styling:

---SECTION 1: DISCLOSURE BOX---
<div style="background:#fff3cd;border-left:4px solid #ffc107;padding:15px;margin:20px 0;border-radius:4px"><strong>Disclosure:</strong> As an Amazon Associate I earn from qualifying purchases at no extra cost to you.</div>

---SECTION 2: INTRO (2-3 paragraphs)---
{intro_hook} Use <strong> for key phrases.

---SECTION 3: QUICK ANSWER BOX---
<div style="background:#e8f4fd;border-left:4px solid #2196f3;padding:15px;margin:20px 0;border-radius:4px"><strong>Quick Answer:</strong> The [Product #1 name] is the best overall pick. [One sentence why — fit, price, reviews].</div>

---SECTION 4: WHAT TO LOOK FOR (H2)---
<h2>What to Look for Before You Buy</h2>
3 numbered tips specific to this product category. Each with a heading and 2-3 bullet sub-points.

---SECTION 5: COMPARISON TABLE (H2)---
<h2>Quick Comparison — All {n} Picks</h2>
<table style="width:100%;border-collapse:collapse;margin:20px 0">
<tr style="background:#2196f3;color:white;text-align:left"><th style="padding:10px">Organizer</th><th style="padding:10px">Best For</th><th style="padding:10px">Price</th><th style="padding:10px">Rating</th></tr>
[alternating rows: white and #f8f9fa, padding:10px, each product]
</table>

---SECTION 6: NUMBERED PRODUCTS (repeat for each of the {n} products)---
For product #1: <h2>#1 — Best Overall: [Product Name]</h2>
For product #2: <h2>#2 — Best for [specific use]: [Product Name]</h2>
For product #3+: <h2>#3 — [Best adjective]: [Product Name]</h2>
(continue pattern for all {n} products)

Each product block MUST follow this EXACTLY (no author name, no byline, no attribution):
<img src="[EXACT image_url from product list]" style="float:right;width:250px;margin:0 0 15px 20px;border-radius:8px" alt="[product name]">
<p>[2-3 sentence expert description — mention specific dimensions, materials, capacity, or unique feature]</p>
<p><strong>Best for:</strong> [specific type of person or home situation]</p>
<p><strong>Pros:</strong></p>
<ul>
<li>[Specific pro 1 — mention actual feature, e.g. "Fits standard 12-inch drawer perfectly"]</li>
<li>[Specific pro 2 — e.g. "BPA-free clear plastic shows contents at a glance"]</li>
<li>[Specific pro 3 — e.g. "Stackable design saves 40% more cabinet space"]</li>
<li>[Specific pro 4 — e.g. "Built-in handles make it easy to pull out and carry"]</li>
<li>[Specific pro 5 — e.g. "Dishwasher-safe for easy cleaning"]</li>
</ul>
<p><strong>Cons:</strong></p>
<ul>
<li>[Honest con 1 — e.g. "Lid is sold separately"]</li>
<li>[Honest con 2 — e.g. "May be too wide for compact drawers under 10 inches"]</li>
</ul>
<p><strong>Price:</strong> [price] &nbsp;|&nbsp; <strong>Rating:</strong> ⭐ [rating] ([estimated],000+ reviews)</p>
<div style="clear:both"></div>
<div style="text-align:center;margin:20px 0">
<a href="[EXACT affiliate_link]" style="background:#ff9900;color:white;padding:12px 25px;border-radius:5px;text-decoration:none;display:inline-block;font-weight:bold;font-size:16px">✅ Check Price on Amazon →</a>
</div>
<hr style="margin:30px 0;border:none;border-top:1px solid #eee">

---SECTION 7: PRO TIPS (H2)---
<h2>5 Pro Tips to Maximize [topic] Space</h2>
Numbered list of 5 actionable, specific tips. Each tip name in bold with 1-2 sentence explanation.

---SECTION 8: FAQ (H2)---
<h2>Frequently Asked Questions</h2>
5 Q&A pairs. Q in bold, answer in plain text. Specific questions someone would actually search.
Format: <p><strong>[Question]</strong></p><p>[Answer]</p>

---SECTION 9: FINAL VERDICT (H2)---
<h2>Final Verdict</h2>
4-5 sentences. Recommend #1 for most people, then mention who should choose #2, #3 alternatives.
End with a motivational closing line.

---SECTION 10: SHOP ALL LINKS---
<h2>Shop All {n} Picks on Amazon</h2>
Numbered list with <a href="[affiliate_link]">[Product name]</a> — [one word best for]

---SECTION 11: FINAL DISCLAIMER---
<p style="font-size:12px;color:#666;margin-top:30px">As an Amazon Associate I earn from qualifying purchases. Prices shown are approximate and may vary. Always check Amazon for current pricing.</p>

REQUIREMENTS:
- US English only
- Return ONLY HTML content (no html/head/body tags, no markdown, no explanation)
- Use EXACT image URLs and affiliate links provided — do not make up URLs
- Total: 2000-2500 words
- Target keywords: {blog_title.lower()}, best {category} organizers, amazon organizers 2026
- CRITICAL: Do NOT add any author name, byline, "by [name]", or attribution ANYWHERE in the blog
- CRITICAL: ALL 11 SECTIONS must be present and complete — do not stop early
- CRITICAL: Every product must have EXACTLY 4-5 pros and EXACTLY 2-3 cons — be specific, not generic"""

    return ask_groq(prompt, max_tokens=8192)


def _fill_freepik_template(template, image_headline, tips=None):
    """Inject the actual image_headline into a freepik template.
    Replaces all [N-WORD HEADLINE/WHATEVER] patterns with image_headline.
    Replaces [SPECIFIC TIP] with provided tips (Tips List style).
    This is done in Python — NOT by Groq — so title and image always match.
    """
    import re
    result = template
    # Replace [X-WORD HEADLINE], [X-WORD ASPIRATIONAL HEADLINE], etc.
    result = re.sub(r'\[\d+-WORD [A-Z /]+\]', image_headline, result)
    result = result.replace('[HEADLINE]', image_headline)
    # Replace [5-WORD WARNING HEADLINE], [5-WORD DEAL HEADLINE], etc.
    result = re.sub(r'\[\d+-WORD [A-Z ]+HEADLINE\]', image_headline, result)
    # Replace problem/statement style placeholders
    result = re.sub(r'\[\d+-WORD [A-Z ]+STATEMENT\]', image_headline, result)
    # Replace tips (only Tips List style has these)
    if tips:
        for tip in tips:
            result = result.replace('[SPECIFIC TIP]', tip, 1)
    # Fallback: replace any remaining [ALL CAPS BRACKET] with image_headline
    result = re.sub(r'\[[A-Z][A-Z /\-]*\]', image_headline, result)
    return result


def generate_pin_content(blog_title, category, blog_url, products, blog_number=1):
    """Generate 10 SEO-optimized pins.

    Two-step approach:
    1. Groq writes: title, image_headline, description, hashtags, tips
    2. Python builds freepik_prompt from the style template + image_headline
       This guarantees title ↔ image ↔ description are always cohesive.
    """
    board_id = BOARDS.get(category, BOARDS['general'])

    p1 = products[0] if len(products) > 0 else {}
    p2 = products[1] if len(products) > 1 else {}
    p3 = products[2] if len(products) > 2 else {}
    n1 = p1.get('name', 'organizer')[:35]
    n2 = p2.get('name', 'organizer')[:35]
    n3 = p3.get('name', 'organizer')[:35]
    pr1 = p1.get('price', '$15')
    pr2 = p2.get('price', '$20')
    pr3 = p3.get('price', '$25')
    r1  = p1.get('rating', '4.5')
    r2  = p2.get('rating', '4.3')
    r3  = p3.get('rating', '4.4')
    n_products = len(products)

    # Extract the specific sub-topic from the blog title (e.g. "refrigerator", "spice cabinet")
    # This is used as the room phrase in ALL Freepik image templates and title rules
    room = extract_topic(blog_title, category)
    print(f"  Topic detected: '{room}' (from blog title)")

    # Fetch trending keywords
    print("  Fetching trending keywords for SEO...")
    trending = get_trending_keywords(blog_title, category)
    trending_str = ", ".join(f'"{kw}"' for kw in trending) if trending else f'"best {category} organizer 2026"'

    # Get category-ordered styles, then ROTATE by blog_number so each blog
    # gets a different starting style — prevents all blog pin-1 being STOP HOOK, etc.
    order = STYLE_ORDERS.get(category, STYLE_ORDERS['general'])
    shift = (blog_number - 1) % len(order)
    order = order[shift:] + order[:shift]

    all_styles = get_style_definitions(room, category, n_products, n1, n2, n3, pr1, pr2, pr3, r1, r2, r3)
    # room_visual already baked into style templates via get_room_visual() call inside get_style_definitions
    ordered_styles = [all_styles[i] for i in order]

    # Build per-pin title rules only (NO freepik in Groq prompt)
    pin_rules = ""
    for slot, style in enumerate(ordered_styles, 1):
        extra_note = ' Also provide "tips": ["tip 1", "tip 2", "tip 3"] (3 specific actionable tips for this category).' if style["name"] == "TIPS LIST" else ' Set "tips": [].'
        pin_rules += f"\nPIN {slot} — {style['name']}: {style['title_rule']}.{extra_note}\n"

    prompt = f"""You are a Pinterest SEO expert targeting US home organization shoppers in 2026.
Blog: "{blog_title}"
Category: {category}
SPECIFIC TOPIC: "{room}" — EVERY pin title and image_headline MUST mention "{room}", NOT just generic "{category}".
Top 3 products: {n1} ({pr1}, {r1}★), {n2} ({pr2}, {r2}★), {n3} ({pr3}, {r3}★)
Total products: {n_products}
Website: smarthomeorganizing.com

Trending searches RIGHT NOW:
{trending_str}

Generate exactly 10 Pinterest pins. Each has 5 fields:

1. "title" — max 100 chars. RULES:
   - MUST include "2026" OR a price like "{pr1}" OR "Amazon" in at least 6 of the 10 pins
   - MUST reference "{room}" specifically
   - Use US buyer language: "Best", "Top", "Under $X", "Worth It", "Actually Work", "Ranked"
   - NO two pins share the same opening word
   - Follow the pin's specific TITLE RULE below

2. "image_headline" — 4-6 words ALL CAPS. MUST contain "{room.upper().split()[0]}" or synonym.

3. "description" — max 500 chars:
   - OPEN with a question US buyers ask: "Tired of...", "Still wasting money on...", "Looking for the best..."
   - Include the price of the top product ({pr1}) naturally
   - Mention "Amazon" at least once
   - 2-3 sentences max
   - End with "→ Full list + Amazon links in bio!"

4. "hashtags" — 12 hashtags as one string. MUST include:
   #HomeOrganization2026 #AmazonHome #AmazonFinds #OrganizationIdeas #HomeOrganization
   Plus 7 niche tags specific to "{room}" and {category}

5. "tips" — array of 3 short actionable tips (only for TIPS LIST style, else [])

TITLE RULES — follow exactly:
{pin_rules}

COHESION: title → image_headline → description must tell ONE unified story about "{room}".
BAD: title "Stop Wasting Kitchen Space" → image_headline "DREAM KITCHEN ORGANIZATION" (too generic)
GOOD: title "Best {room} Organizers 2026 (Tested on Amazon)" → image_headline "BEST {room.upper().split()[0]} ORGANIZERS" → description "Tired of {room}s that waste space? We tested {n_products} top-rated Amazon picks..."

Return ONLY a valid JSON array of 10 objects. No markdown, no explanation."""

    raw = ask_groq(prompt)

    # Extract JSON
    try:
        start = raw.find('[')
        end = raw.rfind(']') + 1
        pins_data = json.loads(raw[start:end])
    except Exception:
        pins_data = []

    # Get Pinterest topic tags for this category
    topic_tags = TOPIC_TAGS.get(category, TOPIC_TAGS["general"])

    # Build pins: Python constructs freepik_prompt from template + Groq's image_headline
    pins = []
    for i, pin in enumerate(pins_data):
        style = ordered_styles[i] if i < len(ordered_styles) else {"name": "", "freepik": ""}
        image_headline = pin.get("image_headline", "").upper().strip()
        tips = pin.get("tips", [])
        freepik_prompt = _fill_freepik_template(style["freepik"], image_headline, tips)

        pins.append({
            "pin_number":     i + 1,
            "style":          style["name"],
            "title":          pin.get("title", ""),
            "image_headline": image_headline,
            "description":    pin.get("description", "") + f"\n\n{pin.get('hashtags', '')}",
            "freepik_prompt": freepik_prompt,
            "link":           blog_url,
            "board_id":       board_id,
            "topic_tags":     topic_tags,
            "category":       category,
            "image_url":      "",
            "posted":         False
        })

    return pins
