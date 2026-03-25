import requests
import json
import time

BASE_URL = "http://localhost:5005"

def test_shorten_and_redirect():
    # A URL that redirects and has tracking info
    # We'll use a local mock or a known stable redirect if testing against live
    # For this test, we'll just check if it correctly "cleans" a simulated URL
    target_url = "https://example.com/path?utm_source=test&fbclid=123&keep=this"
    
    print(f"Shortening: {target_url}")
    response = requests.post(f"{BASE_URL}/shorten", json={"url": target_url})
    
    if response.status_code != 200:
        print(f"FAILED: Status code {response.status_code}")
        print(response.text)
        return False
        
    data = response.json()
    short_code = data.get("short_code")
    short_url = data.get("url")
    
    print(f"Short code: {short_code}")
    print(f"Short URL: {short_url}")
    
    # Verify redirect
    print(f"Verifying redirect for {short_code}...")
    # allow_redirects=False to inspect headers
    redirect_resp = requests.get(f"{BASE_URL}/{short_code}", allow_redirects=False)
    
    if redirect_resp.status_code != 302:
        print(f"FAILED: Expected 302, got {redirect_resp.status_code}")
        return False
        
    location = redirect_resp.headers.get("Location")
    referrer_policy = redirect_resp.headers.get("Referrer-Policy")
    
    print(f"Redirect Location: {location}")
    print(f"Referrer-Policy: {referrer_policy}")
    
    # Expected: example.com/path?keep=this (utm_source and fbclid stripped)
    # Note: requests.get(url, allow_redirects=True).url might resolve example.com to www.example.com etc.
    # But clean_url should have worked on the resolved URL.
    
    if "utm_source" in location or "fbclid" in location:
        print("FAILED: Tracking parameters NOT stripped!")
        return False
        
    if "keep=this" not in location:
        print("FAILED: Important parameters were stripped!")
        return False
        
    # --- Bot Verification ---
    print("\nVerifying bot preview (Slackbot)...")
    bot_resp = requests.get(f"{BASE_URL}/{short_code}", headers={"User-Agent": "Slackbot 1.0"})
    
    if bot_resp.status_code != 200:
        print(f"FAILED: Expected 200 for bot, got {bot_resp.status_code}")
        return False
        
    if "<meta property=\"og:title\"" not in bot_resp.text:
        print("FAILED: OG tags NOT found in bot response!")
        return False
        
    print("SUCCESS: Bot preview verified!")
    return True

if __name__ == "__main__":
    # Wait for service to be up
    time.sleep(2) 
    try:
        if test_shorten_and_redirect():
            print("Verification passed!")
        else:
            exit(1)
    except Exception as e:
        print(f"Error during verification: {e}")
        exit(1)
