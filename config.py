import os

# ─── API KEYS (loaded from GitHub Secrets) ───────────────────────────────────
GROQ_API_KEY       = os.environ.get('GROQ_API_KEY', '')
FREEPIK_API_KEY    = os.environ.get('FREEPIK_API_KEY', '')
BLOGGER_BLOG_ID    = os.environ.get('BLOGGER_BLOG_ID', '1354075857324161808')
MAKE_WEBHOOK_URL   = os.environ.get('MAKE_WEBHOOK_URL', '')
GOOGLE_CREDENTIALS = os.environ.get('GOOGLE_CREDENTIALS_JSON', '')  # contents of credentials.json

# ─── GROQ ─────────────────────────────────────────────────────────────────────
GROQ_MODEL = 'llama-3.3-70b-versatile'

# ─── FREEPIK ──────────────────────────────────────────────────────────────────
IMAGE_WIDTH  = 1000
IMAGE_HEIGHT = 1500  # 2:3 ratio — Pinterest optimal

# ─── PINTEREST BOARDS ────────────────────────────────────────────────────────
BOARDS = {
    'kitchen'  : 'kitchen-organization-ideas',
    'bathroom' : 'bathroom-storage-solutions',
    'bedroom'  : 'closet-organization',
    'office'   : 'home-office-organization',
    'living'   : 'home-organization-tips',
    'kids'     : 'home-organization-tips',
    'spring'   : 'home-organization-tips',
    'budget'   : 'budget-home-organization',
    'general'  : 'home-organization-tips',
    'garage'   : 'home-organization-tips',
    'laundry'  : 'home-organization-tips',
}

# ─── BLOG ─────────────────────────────────────────────────────────────────────
BLOG_URL = 'https://smarthomeorganizing.blogspot.com'
