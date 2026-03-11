import os
from dotenv import load_dotenv
load_dotenv()  # auto-loads .env file — no manual export needed

# ─── API KEYS (loaded from .env locally / GitHub Secrets in CI) ──────────────
GROQ_API_KEY       = os.environ.get('GROQ_API_KEY', '')
FREEPIK_API_KEY    = os.environ.get('FREEPIK_API_KEY', '')
SCRAPER_API_KEY    = os.environ.get('SCRAPER_API_KEY', '')
BLOGGER_BLOG_ID    = os.environ.get('BLOGGER_BLOG_ID', '1354075857324161808')
MAKE_WEBHOOK_URL   = os.environ.get('MAKE_WEBHOOK_URL', '')
GOOGLE_CREDENTIALS  = os.environ.get('GOOGLE_CREDENTIALS_JSON', '')  # contents of credentials.json
GOOGLE_SHEET_URL    = os.environ.get('GOOGLE_SHEET_URL', '')         # your product Google Sheet URL

# ─── GROQ ─────────────────────────────────────────────────────────────────────
GROQ_MODEL = 'llama-3.3-70b-versatile'

# ─── FREEPIK ──────────────────────────────────────────────────────────────────
IMAGE_WIDTH  = 1000  # 2:3 portrait ratio (Pinterest optimal)
IMAGE_HEIGHT = 1440  # Freepik max = 1440 → gives ~1:1.44 ≈ 2:3

# ─── PINTEREST BOARDS ────────────────────────────────────────────────────────
# Numeric board IDs required by Pinterest API
BOARDS = {
    'kitchen'  : '1133007287445630608',
    'bathroom' : '1133007287445630616',
    'bedroom'  : '1133007287445630613',  # Closet Organization Systems
    'office'   : '1133007287445630619',
    'living'   : '1133007287445630611',  # Home Organization Tips
    'kids'     : '1133007287445630611',
    'spring'   : '1133007287445630611',
    'budget'   : '1133007287445630618',
    'general'  : '1133007287445630611',
    'garage'   : '1133007287445630611',
    'laundry'  : '1133007287445630611',
    'amazon'   : '1133007287445633719',
    'finds'    : '1133007287445633719',
}

# ─── PINTEREST TOPIC TAGS (Pinterest's fixed taxonomy — max 10 per pin) ──────
# These are the EXACT strings Pinterest accepts. Do not invent new ones.
TOPIC_TAGS = {
    'kitchen'  : ['home_decor', 'organization', 'cleaning_and_organizing', 'kitchen', 'storage_ideas', 'home_improvement', 'diy_and_crafts'],
    'bathroom' : ['home_decor', 'organization', 'cleaning_and_organizing', 'bathroom', 'storage_ideas', 'home_improvement'],
    'bedroom'  : ['home_decor', 'organization', 'bedroom', 'closet', 'storage_ideas', 'interior_design'],
    'office'   : ['home_decor', 'organization', 'home_office', 'productivity', 'storage_ideas', 'diy_and_crafts'],
    'living'   : ['home_decor', 'organization', 'living_room', 'interior_design', 'storage_ideas'],
    'garage'   : ['home_improvement', 'organization', 'diy_and_crafts', 'garage', 'storage_ideas'],
    'laundry'  : ['home_decor', 'organization', 'cleaning_and_organizing', 'laundry_room', 'storage_ideas'],
    'budget'   : ['home_decor', 'organization', 'budget_decorating', 'cleaning_and_organizing', 'storage_ideas'],
    'amazon'   : ['home_decor', 'organization', 'amazon_finds', 'cleaning_and_organizing', 'storage_ideas'],
    'general'  : ['home_decor', 'organization', 'cleaning_and_organizing', 'interior_design', 'storage_ideas'],
}

# ─── BLOG ─────────────────────────────────────────────────────────────────────
BLOG_URL = 'https://smarthomeorganizing.blogspot.com'
