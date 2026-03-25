import re
import random
import string
import requests
from flask import Flask, request, redirect, jsonify, make_response
from pymongo import MongoClient
from config import (
    MONGO_URI, DATABASE_NAME, COLLECTION_NAME, FLASK_HOST, 
    FLASK_PORT, FLASK_DEBUG, SECRET_KEY, MAX_REDIRECTS, 
    SHORT_CODE_LENGTH, RESOLVE_STOP_KEYWORDS
)
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse, urljoin

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# Silencing Flask's default logging to maintain "zero logs" requirement
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# MongoDB Setup
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
urls_collection = db[COLLECTION_NAME]

import hashlib

# Tracking parameters and fragments to strip
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "utm_name", "utm_cid", "utm_reader", "utm_referrer",
    "gclid", "dclid", "fbclid", "mc_cid", "mc_eid", "igshid", "mkt_tok",
    "yclid", "_hsenc", "_hsmi", "vero_id", "rb_clickid", "s_cid",
    "cmpid", "campaign_id", "ad_id", "adset_id", "ref", "ref_src",
    "source", "si", "spm"
}

def resolve_url(url, timeout=10):
    """
    Follow redirects to find the final destination, but stop early if we hit 
    an authentication gate (Smart Stop).
    """
    metadata = {"title": "", "description": "", "image": ""}
    current_url = url
    ua_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        # Step 1: Manually follow redirects to inspect for "Smart Stop" keywords
        for _ in range(MAX_REDIRECTS):
            # We use allow_redirects=False to check each hop for login patterns
            r = requests.head(current_url, allow_redirects=False, timeout=timeout, headers=ua_headers)
            
            if r.status_code in [301, 302, 303, 307, 308]:
                next_url = r.headers.get('Location')
                if not next_url:
                    break
                
                # Handle relative redirects
                if not next_url.startswith(('http://', 'https://')):
                    next_url = urljoin(current_url, next_url)
                
                # SMART STOP: If the next hop looks like a login/auth page, 
                # we stop resolving and stick with the current "clean" URL.
                if any(kw in next_url.lower() for kw in RESOLVE_STOP_KEYWORDS):
                    break
                
                current_url = next_url
            else:
                # No more redirects, this is the final page
                break
        
        # Step 2: Extract metadata from the final resolved (or stopped) page
        r = requests.get(current_url, allow_redirects=True, timeout=timeout, headers=ua_headers)
        final_url = r.url
        
        # Extract title using basic regex
        title_match = re.search(r'<title>(.*?)</title>', r.text, re.I | re.S)
        if title_match:
            metadata["title"] = title_match.group(1).strip()
            
        # Extract OG tags (Open Graph) for chat app previews
        og_tags = {
            "title": re.search(r'<meta [^>]*property=["\']og:title["\'] [^>]*content=["\'](.*?)["\']', r.text, re.I),
            "description": re.search(r'<meta [^>]*property=["\']og:description["\'] [^>]*content=["\'](.*?)["\']', r.text, re.I),
            "image": re.search(r'<meta [^>]*property=["\']og:image["\'] [^>]*content=["\'](.*?)["\']', r.text, re.I)
        }
        
        for key, match in og_tags.items():
            if match:
                metadata[key] = match.group(1).strip()
                
        return final_url, metadata
    except Exception:
        # If anything fails during resolution, return what we have
        return current_url, metadata

def clean_url(url):
    """Strip tracking data and normalize the URL."""
    try:
        parsed = urlparse(url)

        # remove common tracking params
        clean_query = []
        for k, v in parse_qsl(parsed.query, keep_blank_values=True):
            if k.lower() not in TRACKING_PARAMS and not k.lower().startswith("utm_"):
                clean_query.append((k, v))

        # strip fragments often used for tracking
        fragment = ""
        if parsed.fragment and not re.match(r"^(xtor|utm_)", parsed.fragment, re.I):
            fragment = parsed.fragment

        # normalize host
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]

        # remove default ports
        netloc = netloc.replace(":80", "").replace(":443", "")

        # collapse duplicate slashes in path
        path = re.sub(r"/{2,}", "/", parsed.path or "/")

        cleaned = parsed._replace(
            netloc=netloc,
            query=urlencode(clean_query, doseq=True),
            fragment=fragment,
            path=path
        )
        return urlunparse(cleaned)
    except Exception:
        return url

def generate_short_code(url, length=8):
    """Create a deterministic short code from the URL."""
    return hashlib.sha256(url.encode()).hexdigest()[:length]

@app.route('/')
def index():
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>URL Cleaner & Shortener</title>
    <style>
        body { font-family: 'Inter', sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #121212; color: #e0e0e0; }
        form { background: #1e1e1e; padding: 2.5rem; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.4); width: 450px; display: flex; flex-direction: column; border: 1px solid #333; }
        h2 { margin-top: 0; color: #bb86fc; font-weight: 300; letter-spacing: 1px; }
        input { padding: 0.8rem; margin-bottom: 1.5rem; border: 1px solid #333; border-radius: 6px; background: #2c2c2c; color: #fff; font-size: 1rem; }
        input:focus { outline: none; border-color: #bb86fc; box-shadow: 0 0 0 2px rgba(187, 134, 252, 0.2); }
        button { padding: 0.8rem; background: #bb86fc; color: #000; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 1rem; transition: background 0.2s; }
        button:hover { background: #9965f4; }
    </style>
</head>
<body>
    <form action="/shorten" method="POST">
        <h2>Clean & Shorten</h2>
        <input type="text" name="url" placeholder="Paste URL here..." required>
        <button type="submit">Shorten</button>
    </form>
</body>
</html>"""

@app.route('/shorten', methods=['POST'])
def shorten():
    # Handle both JSON and Form data
    if request.is_json:
        data = request.get_json()
        target_url = data.get('url', '').strip()
    else:
        target_url = request.form.get('url', '').strip()
    
    if not target_url:
        return jsonify({"error": "URL is required"}), 400
        
    # Add protocol if missing
    if not target_url.startswith(('http://', 'https://')):
        target_url = f"https://{target_url}"
    
    # 1. Resolve final destination and metadata
    resolved_url, metadata = resolve_url(target_url)
    
    # 2. Clean tracking data
    cleaned_url = clean_url(resolved_url)
    
    # 3. Generate deterministic short code
    short_code = generate_short_code(cleaned_url, length=SHORT_CODE_LENGTH)
    
    # 4. Store
    urls_collection.update_one(
        {"short_code": short_code},
        {"$set": {
            "target": cleaned_url,
            "original": target_url,
            "metadata": metadata
        }},
        upsert=True
    )
    
    short_url = f"{request.host_url}{short_code}"
    
    if request.is_json:
        return jsonify({"short_code": short_code, "url": short_url})
    else:
        # Return simple HTML result page for browser users
        return f"""<!DOCTYPE html><html>
        <head>
            <style>
                body {{ font-family: 'Inter', sans-serif; background: #121212; color: #e0e0e0; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
                .card {{ background: #1e1e1e; padding: 2.5rem; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.4); width: 500px; border: 1px solid #333; }}
                h2 {{ color: #03dac6; margin-top: 0; }}
                p {{ margin: 0.8rem 0; font-size: 0.9rem; color: #aaa; }}
                .url-box {{ background: #2c2c2c; padding: 0.8rem; border-radius: 6px; word-break: break-all; color: #fff; border: 1px solid #333; margin-top: 0.5rem; }}
                a {{ color: #bb86fc; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                .back {{ display: inline-block; margin-top: 1.5rem; color: #bb86fc; font-weight: bold; }}
            </style>
        </head>
        <body>
        <div class="card">
            <h2>URL Shortened!</h2>
            <p><strong>Original Destination:</strong></p>
            <div class="url-box">{target_url}</div>
            <p><strong>Cleaned Destination:</strong></p>
            <div class="url-box">{cleaned_url}</div>
            <p><strong>Shortened Link:</strong></p>
            <div class="url-box"><a href="{short_url}">{short_url}</a></div>
            <a href="/" class="back">← Create Another</a>
        </div>
        </body></html>"""

BOT_AGENTS = [
    'facebookexternalhit', 'Twitterbot', 'Slackbot', 'Discordbot', 
    'WhatsApp', 'TelegramBot', 'LinkedInBot', 'Pinterest'
]

@app.route('/<path:code_or_url>')
def do_redirect(code_or_url):
    # Support both short codes and direct URLs passed in the path
    # If there's a query string, we should append it back if it's a direct URL
    full_path = code_or_url
    if request.query_string:
        full_path += f"?{request.query_string.decode()}"
        
    mapping = urls_collection.find_one({"short_code": code_or_url})
    
    if not mapping:
        # If not a short code, check if it looks like a URL to be cleaned
        if '.' in code_or_url or code_or_url.startswith(('http://', 'https://')):
            target_url = full_path
            if not target_url.startswith(('http://', 'https://')):
                target_url = f"https://{target_url}"
                
            # Resolve and clean on the fly
            resolved_url, _ = resolve_url(target_url)
            cleaned_url = clean_url(resolved_url)
            target = cleaned_url
        else:
            return "Not Found", 404
    else:
        target = mapping['target']
    
    ua = request.headers.get('User-Agent', '')
    is_bot = any(bot in ua for bot in BOT_AGENTS)
    
    if is_bot:
        meta = mapping.get('metadata', {}) if mapping else {}
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{meta.get('title', 'Redirecting...')}</title>
    <meta property="og:title" content="{meta.get('title', '')}">
    <meta property="og:description" content="{meta.get('description', '')}">
    <meta property="og:image" content="{meta.get('image', '')}">
    <meta property="og:url" content="{target}">
    <meta property="og:type" content="website">
    <meta http-equiv="refresh" content="0; url={target}">
</head>
<body>
    Redirecting to <a href="{target}">{target}</a>
</body>
</html>"""
        return html
    
    # Create valid 302 redirect for humans
    response = make_response(redirect(target, code=302))
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response

if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
